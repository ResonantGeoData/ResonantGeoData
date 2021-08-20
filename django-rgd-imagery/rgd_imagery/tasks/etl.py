"""Helper methods for creating a ``GDALRaster`` entry from a raster file."""
from contextlib import contextmanager
import os
import tempfile

from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry, Polygon
import numpy as np
from osgeo import gdal
import rasterio
from rasterio import Affine, MemoryFile
import rasterio.features
import rasterio.shutil
import rasterio.warp
from rasterio.warp import Resampling, calculate_default_transform, reproject
from rgd.models.constants import DB_SRID
from rgd.utility import get_or_create_no_commit
from rgd_imagery.large_image_utilities import get_tile_bounds, yeild_tilesource_from_image
from rgd_imagery.models import BandMeta, Image, ImageMeta, Raster, RasterMeta
from shapely.geometry import shape
from shapely.ops import unary_union

logger = get_task_logger(__name__)

GDAL_DATA = os.path.join(os.path.dirname(rasterio.__file__), 'gdal_data')
os.environ['GDAL_DATA'] = GDAL_DATA


MAX_LOAD_SHAPE = (4000, 4000)


def _populate_image_meta_models(image, image_meta):

    with yeild_tilesource_from_image(image) as tile_source:
        meta = tile_source.getMetadata()
        imeta = tile_source.getInternalMetadata()
        bands = tile_source.getBandInformation()

        image_meta.number_of_bands = len(bands)
        image_meta.driver = (
            imeta['driverShortName'] if 'driverShortName' in imeta else 'pil'
        )  # NOTE: assumes PIL if not using GDAL
        image_meta.height = meta['sizeY']
        image_meta.width = meta['sizeX']
        # No longer editing image_entry
        image_meta.save()

        # TODO: we need `PILFileTileSource` in large_image to support band information
        if 'bands' in meta:
            for index, band_info in bands.items():

                def safe_get(key):
                    return band_info[key] if key in band_info else None

                band_meta = BandMeta()
                band_meta.parent_image = image_meta.parent_image
                band_meta.band_number = index
                band_meta.nodata_value = safe_get('nodata')
                band_meta.min = safe_get('min')
                band_meta.max = safe_get('max')
                band_meta.mean = safe_get('mean')
                band_meta.std = safe_get('stdev')
                band_meta.interpretation = safe_get('interpretation')
                # Save this band entirely
                band_meta.save()


def load_image(image):
    """Image ingestion routine.

    This helper will open an image file from ``Image`` and create a
    ``ImageMeta`` and collection of ``BandMeta`` entries.

    """
    # Fetch the image file this Layer corresponds to
    if not isinstance(image, Image):
        image = Image.objects.get(id=image)

    image_meta, created = get_or_create_no_commit(ImageMeta, parent_image=image)
    if not created:
        # Clear out associated entries because they could be invalid
        BandMeta.objects.filter(parent_image=image).delete()

    _populate_image_meta_models(image, image_meta)

    return image_meta


def _extract_raster_outline(tile_source):
    bounds = get_tile_bounds(tile_source)
    coords = np.array(
        (
            (bounds['xmin'], bounds['ymax']),
            (bounds['xmin'], bounds['ymax']),
            (bounds['xmax'], bounds['ymax']),
            (bounds['xmax'], bounds['ymin']),
            (bounds['xmin'], bounds['ymin']),
            (bounds['xmin'], bounds['ymax']),  # Close the loop
        )
    )
    return Polygon(coords)


def _extract_raster_meta(image):
    """Extract all of the raster meta info in our models from an Image.

    The keys of the returned dict should match the fields of the
    ``Raster``.

    """
    raster_meta = dict()

    with yeild_tilesource_from_image(image) as tile_source:
        meta = tile_source.getMetadata()
        imeta = tile_source.getInternalMetadata()
        bounds = get_tile_bounds(tile_source)

        raster_meta['crs'] = tile_source.getProj4String()
        raster_meta['origin'] = [bounds['xmin'], bounds['ymin']]
        raster_meta['resolution'] = (meta['mm_x'] * 0.001, meta['mm_y'] * 0.001)  # meters
        raster_meta['transform'] = imeta['GeoTransform']
        raster_meta['extent'] = [
            bounds['xmin'],
            bounds['ymin'],
            bounds['xmax'],
            bounds['ymax'],
        ]
        raster_meta['outline'] = _extract_raster_outline(tile_source)
        raster_meta['footprint'] = raster_meta['outline']

    return raster_meta


def _get_valid_data_footprint(src, band_num):
    """Get ``GEOSGeometry`` of valid data footprint from the raster mask."""
    # Determine mask resolution to prevent loading massive imagery
    # shape = tuple(np.min([src.shape, MAX_LOAD_SHAPE], axis=0))
    # mask = src.read_masks(band_num, out_shape=shape, resampling=5)
    # TODO: fix transform to match this resampling
    nodata = 0
    if not src.nodata:
        workdir = getattr(settings, 'GEODATA_WORKDIR', None)
        with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
            output_path = os.path.join(tmpdir, 'temp')
            rasterio.shutil.copy(src, output_path, driver=src.driver)
            with rasterio.open(output_path, 'r+') as src:
                nodata = 0
                src.nodata = nodata
                mask = src.dataset_mask()
    else:
        nodata = src.nodata
        mask = src.dataset_mask()

    # Extract feature shapes and values from the array.
    # Assumes already working in correct spatial reference
    geoms = []
    for geom, val in rasterio.features.shapes(mask, transform=src.transform):
        # Ignore the 0-feature and only return on valid data feature
        if val != nodata:
            geoms.append(shape(geom))
    if geoms:
        geom = unary_union(geoms)
        return GEOSGeometry(geom.to_wkt()).convex_hull

    raise ValueError('No valid raster footprint found.')


@contextmanager
def _yield_downsampled_raster(raster):
    # https://gis.stackexchange.com/questions/329434/creating-an-in-memory-rasterio-dataset-from-numpy-array/329439#329439
    max_n = np.product(MAX_LOAD_SHAPE)
    n = raster.height * raster.width
    scale = 1.0
    if n > max_n:
        scale = max_n / n

    if scale == 1.0:
        yield raster
        return

    t = raster.transform
    # rescale the metadata
    transform = Affine(t.a / scale, t.b, t.c, t.d, t.e / scale, t.f)
    height = int(raster.height * scale)
    width = int(raster.width * scale)

    profile = raster.profile
    profile.update(transform=transform, height=height, width=width)

    data = raster.read(
        out_shape=(raster.count, height, width),
        resampling=Resampling.bilinear,
    )

    with MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:
            dataset.write(data)
            del data

        with memfile.open() as dataset:  # Reopen as DatasetReader
            yield dataset  # Note yield not return


@contextmanager
def _reproject_raster(file_path, epsg):
    """Reproject an open raster to given spatial reference.

    This will return an open rasterio handle.

    """
    dst_crs = rasterio.crs.CRS.from_epsg(epsg)
    with rasterio.open(file_path, 'r') as src:
        if src.crs == dst_crs:
            # If raster already in desired CRS, return itself
            yield src
            return
        workdir = getattr(settings, 'GEODATA_WORKDIR', None)
        with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
            # Get a downsampled version of the original raster
            with _yield_downsampled_raster(src) as dsrc:
                # If raster is NTIF format, convert first
                if dsrc.driver == 'NITF':
                    f = dsrc.files[0]
                    output_path = os.path.join(tmpdir, os.path.basename(f)) + '.tiff'
                    ds = gdal.Open(f)
                    ds = gdal.Translate(output_path, ds, options=['-of', 'GTiff'])
                    ds = None
                    # TODO: this file is not closed properly.
                    dsrc = rasterio.open(output_path, 'r')

                transform, width, height = calculate_default_transform(
                    dsrc.crs, dst_crs, dsrc.width, dsrc.height, *dsrc.bounds
                )
                kwargs = dsrc.meta.copy()
                kwargs.update(
                    {'crs': dst_crs, 'transform': transform, 'width': width, 'height': height}
                )
                path = os.path.join(tmpdir, 'temp_raster')
                with rasterio.open(path, 'w', **kwargs) as dst:
                    for i in range(1, dsrc.count + 1):
                        reproject(
                            source=rasterio.band(dsrc, i),
                            destination=rasterio.band(dst, i),
                            src_transform=dsrc.transform,
                            src_crs=dsrc.crs,
                            dst_transform=transform,
                            dst_crs=dst_crs,
                            resampling=Resampling.bilinear,
                        )
                    dst.colorinterp = dsrc.colorinterp
            with rasterio.open(path, 'r') as rsrc:
                yield rsrc


def _extract_raster_footprint(image):
    """Extract the footprint of raster's Image.

    This operates on the assumption that the Image is a valid raster.

    """
    with image.file.yield_local_path(vsi=True) as file_path:
        # Reproject the raster to the DB SRID using rasterio directly rather
        #  than transforming the extracted geometry which had issues.
        with _reproject_raster(file_path, DB_SRID) as src:
            try:
                # Only implement for first band for now
                return _get_valid_data_footprint(src, 1)
            except Exception as e:  # TODO: be more clever about this
                logger.error(f'Issue computing valid data footprint: {e}')


def _compare_raster_meta(a, b):
    """Evaluate if the two raster meta dictionaries are equal."""
    keys = a.keys()
    if keys != b.keys():
        # The keys should always be the same...
        # these dicts are generated from `_extract_raster_meta`
        return False
    for k in keys:
        if a[k] != b[k]:
            return False
    return True


def _validate_image_set_is_raster(image_set):
    """Validate if all of the images in a single ``ImageSet`` are a raster.

    Will check if all have a spatial reference/geo meta info but not
    necessarily the same.

    Returns the first image's meta info if it checks out.

    """
    images = list(image_set.images.all())

    if not images:
        raise ValueError('ImageSet returned no images.')

    base_image = images.pop()
    first_meta = _extract_raster_meta(base_image)
    for image in images:
        _extract_raster_meta(image)

    return first_meta


def populate_raster(raster):
    """Autopopulate the fields of the raster."""
    if not isinstance(raster, Raster):
        raster = Raster.objects.get(id=raster)

    if not raster.name:
        raster.name = raster.image_set.name
        raster.save(
            update_fields=[
                'name',
            ]
        )
    # Has potential to error with failure reason
    meta = _validate_image_set_is_raster(raster.image_set)
    raster_meta, created = get_or_create_no_commit(RasterMeta, parent_raster=raster)
    # Not using `defaults` here because we want `meta` to always get updated.
    for k, v in meta.items():
        # Yeah. This is sketchy, but it works.
        setattr(raster_meta, k, v)
    raster_meta.save()
    return True


def populate_raster_outline(raster_id):
    raster = Raster.objects.get(id=raster_id)
    base_image = raster.image_set.images.first()
    with yeild_tilesource_from_image(base_image) as tile_source:
        raster.rastermeta.outline = _extract_raster_outline(tile_source)
    raster.rastermeta.save(
        update_fields=[
            'outline',
        ]
    )


def populate_raster_footprint(raster_id):
    raster = Raster.objects.get(id=raster_id)
    # Only set the footprint if the RasterMeta has been created already
    #   this avoids a race condition where footprint might not get set correctly.
    try:
        raster_meta = RasterMeta.objects.get(parent_raster=raster)
        base_image = raster.image_set.images.first()
        footprint = _extract_raster_footprint(base_image)
        if footprint:
            raster_meta.footprint = footprint
            raster_meta.save(update_fields=['footprint'])
    except RasterMeta.DoesNotExist:
        logger.error('Cannot populate raster footprint yet due to race condition. Try again later.')
