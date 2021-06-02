"""Helper methods for creating a ``GDALRaster`` entry from a raster file."""
from contextlib import contextmanager
import os
import tempfile
import zipfile

from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.gis.geos import (
    GEOSGeometry,
    LineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
import kwcoco
import kwimage
import numpy as np
from osgeo import gdal
import rasterio
from rasterio import Affine, MemoryFile
import rasterio.features
import rasterio.shutil
import rasterio.warp
from rasterio.warp import Resampling, calculate_default_transform, reproject
from shapely.geometry import shape
from shapely.ops import unary_union

from rgd.utility import get_or_create_no_commit

from ..common import ChecksumFile
from ..constants import DB_SRID
from ..geometry.transform import transform_geometry
from .annotation import Annotation, PolygonSegmentation, RLESegmentation, Segmentation
from .base import BandMetaEntry, ImageEntry, ImageFile, ImageSet
from .kwcoco import KWCOCOArchive
from .processed import ConvertedImageFile
from .raster import RasterEntry, RasterMetaEntry

logger = get_task_logger(__name__)

GDAL_DATA = os.path.join(os.path.dirname(rasterio.__file__), 'gdal_data')
os.environ['GDAL_DATA'] = GDAL_DATA


MAX_LOAD_SHAPE = (4000, 4000)


def _read_image_to_entry(image_entry, image_file_path):

    with rasterio.open(image_file_path) as src:
        image_entry.number_of_bands = src.count
        image_entry.driver = src.driver
        image_entry.height = src.shape[0]
        image_entry.width = src.shape[1]

        # A catch-all metadata feild:
        # TODO: image_entry.metadata =

        # These are things I couldn't figure out how to get with gdal directly
        dtypes = src.dtypes
        interps = src.colorinterp

    # No longer editing image_entry
    image_entry.save()

    # Rasterio is no longer open... using gdal directly:
    gsrc = gdal.Open(str(image_file_path))  # Have to cast Path to str

    n = gsrc.RasterCount
    if n != image_entry.number_of_bands:
        # Sanity check
        raise ValueError('gdal detects different number of bands than rasterio.')
    for i in range(n):
        gdal_band = gsrc.GetRasterBand(i + 1)  # off by 1 indexing
        band_meta = BandMetaEntry()
        band_meta.parent_image = image_entry
        band_meta.band_number = i + 1  # off by 1 indexing
        band_meta.description = gdal_band.GetDescription()
        band_meta.nodata_value = gdal_band.GetNoDataValue()
        try:
            band_meta.dtype = dtypes[i]
        except IndexError:
            pass
        # TODO: seperate out band stats into separate tasks
        # bmin, bmax, mean, std = gdal_band.GetStatistics(True, True)
        # band_meta.min = bmin
        # band_meta.max = bmax
        # band_meta.mean = mean
        # band_meta.std = std

        try:
            band_meta.interpretation = interps[i].name
        except IndexError:
            pass

        # Save this band entirely
        band_meta.save()


def read_image_file(ife):
    """Image ingestion routine.

    This helper will open an image file from ``ImageFile`` and create a
    ``ImageEntry`` and collection of ``BandMetaEntry`` entries.

    """
    # Fetch the image file this Layer corresponds to
    if not isinstance(ife, ImageFile):
        ife = ImageFile.objects.get(id=ife)

    with ife.file.yield_local_path(vsi=True) as file_path:
        image_entry, created = get_or_create_no_commit(
            ImageEntry, defaults=dict(name=ife.file.name), image_file=ife
        )
        if not created:
            # Clear out associated entries because they could be invalid
            BandMetaEntry.objects.filter(parent_image=image_entry).delete()
            ConvertedImageFile.objects.filter(source_image=image_entry).delete()

        _read_image_to_entry(image_entry, file_path)

    return image_entry


def _extract_raster_outline(src):
    coords = np.array(
        (
            (src.bounds.left, src.bounds.top),
            (src.bounds.right, src.bounds.top),
            (src.bounds.right, src.bounds.bottom),
            (src.bounds.left, src.bounds.bottom),
            (src.bounds.left, src.bounds.top),  # Close the loop
        )
    )
    return transform_geometry(Polygon(coords, srid=src.crs.to_epsg()), src.crs.to_wkt())


def _extract_raster_meta(image_file_entry):
    """Extract all of the raster meta info in our models from an image file.

    The keys of the returned dict should match the fields of the
    ``RasterEntry``.

    """
    raster_meta = dict()
    with image_file_entry.file.yield_local_path(vsi=True) as path:
        with rasterio.open(path) as src:
            raster_meta['crs'] = src.crs.to_proj4()
            raster_meta['origin'] = [src.bounds.left, src.bounds.bottom]
            raster_meta['extent'] = [
                src.bounds.left,
                src.bounds.bottom,
                src.bounds.right,
                src.bounds.top,
            ]
            raster_meta['resolution'] = src.res
            raster_meta['transform'] = src.transform.to_gdal()  # TODO: check this
            raster_meta['outline'] = _extract_raster_outline(src)
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


def _extract_raster_footprint(image_file_entry):
    """Extract the footprint of raster's image file entry.

    This operates on the assumption that the image file is a valid raster.

    """
    with image_file_entry.file.yield_local_path(vsi=True) as file_path:
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


def _validate_image_set_is_raster(image_set_entry):
    """Validate if all of the images in a single ``ImageSet`` are a raster.

    Will check if all have a spatial reference/geo meta info but not
    necessarily the same.

    Returns the first image's meta info if it checks out.

    """
    images = list(image_set_entry.images.all())

    if not images:
        raise ValueError('ImageSet returned no images.')

    base_image = images.pop()
    first_meta = _extract_raster_meta(base_image.image_file.imagefile)
    for image in images:
        _extract_raster_meta(image.image_file.imagefile)

    return first_meta


def populate_raster_entry(raster_entry):
    """Autopopulate the fields of the raster."""
    if not isinstance(raster_entry, RasterEntry):
        raster_entry = RasterEntry.objects.get(id=raster_entry)

    # Has potential to error with failure reason
    meta = _validate_image_set_is_raster(raster_entry.image_set)
    if not raster_entry.name:
        raster_entry.name = raster_entry.image_set.name
        raster_entry.save(
            update_fields=[
                'name',
            ]
        )
    raster_meta, created = get_or_create_no_commit(RasterMetaEntry, parent_raster=raster_entry)
    # Not using `defaults` here because we want `meta` to always get updated.
    for k, v in meta.items():
        # Yeah. This is sketchy, but it works.
        setattr(raster_meta, k, v)
    raster_meta.save()
    return True


def populate_raster_outline(raster_id):
    raster_entry = RasterEntry.objects.get(id=raster_id)
    base_image = raster_entry.image_set.images.first()
    with base_image.image_file.file.yield_local_path(vsi=True) as path:
        with rasterio.open(path) as src:
            raster_entry.rastermetaentry.outline = _extract_raster_outline(src)
    raster_entry.rastermetaentry.save(
        update_fields=[
            'outline',
        ]
    )


def populate_raster_footprint(raster_id):
    raster_entry = RasterEntry.objects.get(id=raster_id)
    # Only set the footprint if the RasterMetaEntry has been created already
    #   this avoids a race condition where footprint might not get set correctly.
    try:
        raster_meta = RasterMetaEntry.objects.get(parent_raster=raster_entry)
        base_image = raster_entry.image_set.images.first()
        footprint = _extract_raster_footprint(base_image.image_file.imagefile)
        if footprint:
            raster_meta.footprint = footprint
            raster_meta.save(update_fields=['footprint'])
    except RasterMetaEntry.DoesNotExist:
        logger.error('Cannot populate raster footprint yet due to race condition. Try again later.')


def _fill_annotation_segmentation(annotation_entry, ann_json):
    """For converting KWCOCO annotation JSON to an Annotation entry."""
    if 'keypoints' in ann_json and ann_json['keypoints']:
        # populate keypoints - ignore 3rd value visibility
        logger.info('Keypoints: {}'.format(ann_json['keypoints']))
        points = np.array(ann_json['keypoints']).astype(float).reshape((-1, 3))
        keypoints = []
        for pt in points:
            logger.info(f'The Point: {pt}')
            keypoints.append(Point(pt[0], pt[1]))
        annotation_entry.keypoints = MultiPoint(*keypoints)
    if 'line' in ann_json and ann_json['line']:
        # populate line
        points = np.array(ann_json['line']).astype(float).reshape((-1, 2))
        logger.info(f'The line: {points}')
        annotation_entry.line = LineString(*[(pt[0], pt[1]) for pt in points], srid=0)
    # Add a segmentation
    segmentation = None
    if 'segmentation' in ann_json and ann_json['segmentation']:
        sseg = kwimage.Segmentation.coerce(ann_json['segmentation']).data
        if isinstance(sseg, kwimage.Mask):
            segmentation = RLESegmentation()
            segmentation.from_rle(ann_json['segmentation'])
        else:
            segmentation = PolygonSegmentation()
            polys = []
            multipoly = sseg.to_multi_polygon()
            for poly in multipoly.data:
                poly_xys = poly.data['exterior'].data
                # Close the loop
                poly_xys = np.append(poly_xys, poly_xys[0][None], axis=0)
                polys.append(Polygon(poly_xys, srid=0))
            segmentation.feature = MultiPolygon(*polys)
    if 'bbox' in ann_json and ann_json['bbox']:
        if not segmentation:
            segmentation = Segmentation()  # Simple outline segmentation
        # defined as (x, y, width, height)
        x0, y0, w, h = np.array(ann_json['bbox'])
        points = [
            [x0, y0],
            [x0, y0 + h],
            [x0 + w, y0 + h],
            [x0 + w, y0],
            [x0, y0],  # close the loop
        ]
        segmentation.outline = Polygon(points, srid=0)
    annotation_entry.save()
    # Save if a segmentation is used
    if segmentation:
        segmentation.annotation = annotation_entry
        segmentation.save()


def load_kwcoco_dataset(kwcoco_dataset_id):
    logger.info('Starting KWCOCO ETL routine')
    ds_entry = KWCOCOArchive.objects.get(id=kwcoco_dataset_id)
    if not ds_entry.name:
        ds_entry.name = os.path.basename(ds_entry.spec_file.name)
        ds_entry.save(
            update_fields=[
                'name',
            ]
        )

    # TODO: add a setting like this:
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:

        if ds_entry.image_set:
            # Delete all previously existing data
            # This should cascade to all the annotations
            for imageentry in ds_entry.image_set.images.all():
                imageentry.image_file.file.delete()
        else:
            ds_entry.image_set = ImageSet()
        ds_entry.image_set.name = ds_entry.name
        ds_entry.image_set.save()
        ds_entry.save(
            update_fields=[
                'image_set',
            ]  # noqa: E231
        )

        # Unarchive the images locally so we can import them when loading the spec
        # Images could come from a URL, so this is optional
        if ds_entry.image_archive:
            with ds_entry.image_archive.file as file_obj:
                logger.info(f'The KWCOCO image archive: {ds_entry.image_archive}')
                # Place images in a local directory and keep track of root path
                # Unzip the contents to the working dir
                with zipfile.ZipFile(file_obj, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                logger.info(f'The extracted KWCOCO image archive: {tmpdir}')
        else:
            pass
            # TODO: how should we download data from specified URLs?

        # Load the KWCOCO JSON spec and make annotations on the images
        with ds_entry.spec_file.yield_local_path() as file_path:
            ds = kwcoco.CocoDataset(str(file_path))
            # Set the root dir to where the images were extracted / the temp dir
            # If images are coming from URL, they will download to here
            ds.img_root = tmpdir
            # Iterate over images and create an ImageEntry from them.
            # Any images in the archive that aren't listed in the JSON will be deleted
            for imgid in ds.imgs.keys():
                ak = ds.index.gid_to_aids[imgid]
                img = ds.imgs[imgid]
                anns = [ds.anns[k] for k in ak]
                # Create the ImageFile entry to track each image's location
                image_file_abs_path = os.path.join(ds.img_root, img['file_name'])
                name = os.path.basename(image_file_abs_path)
                image_file = ImageFile()
                image_file.collection = ds_entry.spec_file.collection
                image_file.skip_signal = True
                image_file.file = ChecksumFile()
                image_file.file.file.save(name, open(image_file_abs_path, 'rb'))
                image_file.save()
                # Create a new ImageEntry
                image_entry = read_image_file(image_file)
                # Add ImageEntry to ImageSet
                ds_entry.image_set.images.add(image_entry)
                # Create annotations that link to that ImageEntry
                for ann in anns:
                    annotation_entry = Annotation()
                    annotation_entry.image = image_entry
                    try:
                        annotation_entry.label = ds.cats[ann['category_id']]['name']
                    except KeyError:
                        pass
                    # annotation_entry.annotator =
                    # annotation_entry.notes =
                    _fill_annotation_segmentation(annotation_entry, ann)
    logger.info('Done with KWCOCO ETL routine')
