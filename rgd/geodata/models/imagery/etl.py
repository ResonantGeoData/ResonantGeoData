"""Helper methods for creating a ``GDALRaster`` entry from a raster file."""
import io
import json
import os
import tempfile
import zipfile

import PIL.Image
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
from django.core.files.base import ContentFile
import kwcoco
import kwimage
import matplotlib.pyplot as plt
import numpy as np
from osgeo import gdal
import rasterio
import rasterio.features
import rasterio.warp
from rasterio.warp import Resampling, calculate_default_transform, reproject, transform_bounds

from rgd.utility import get_or_create_no_commit

from ..common import ChecksumFile
from ..constants import DB_SRID, WEB_MERCATOR
from .annotation import Annotation, PolygonSegmentation, RLESegmentation, Segmentation
from .base import (
    BandMetaEntry,
    ConvertedImageFile,
    ImageEntry,
    ImageFile,
    ImageSet,
    KWCOCOArchive,
    RasterEntry,
    RasterMetaEntry,
    Thumbnail,
)

logger = get_task_logger(__name__)

GDAL_DATA = os.path.join(os.path.dirname(rasterio.__file__), 'gdal_data')
os.environ['GDAL_DATA'] = GDAL_DATA


MAX_LOAD_SHAPE = (4000, 4000)


def _create_thumbnail_image(src):
    shape = (min(MAX_LOAD_SHAPE[0], src.height), min(MAX_LOAD_SHAPE[0], src.width))

    def get_band(n):
        return src.read(n, out_shape=shape)

    norm = plt.Normalize()

    c = src.colorinterp

    if c[0:3] == (3, 4, 5):
        r = get_band(1)
        g = get_band(2)
        b = get_band(3)
        colors = np.dstack((r, g, b)).astype('uint8')
    elif len(c) == 1 and c[0] == 1:
        # Gray scale
        colors = (norm(get_band(1)) * 255).astype('uint8')
    else:
        colors = (plt.cm.viridis(norm(get_band(1))) * 255).astype('uint8')[:, :, 0:3]

    buf = io.BytesIO()
    img = PIL.Image.fromarray(colors)
    img.save(buf, 'JPEG')
    byte_im = buf.getvalue()
    return ContentFile(byte_im)


def _reproject_raster(src, epsg):
    """Reproject an open raster to given spatial reference.

    This will return an open rasterio handle.

    """
    dst_crs = rasterio.crs.CRS.from_epsg(epsg)
    if src.crs == dst_crs:
        # If raster already in desired CRS, return itself
        return src
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    tmpdir = tempfile.mkdtemp(dir=workdir)
    # If raster is NTIF format, convert first
    if src.driver == 'NITF':
        f = src.files[0]
        output_path = os.path.join(tmpdir, os.path.basename(f)) + '.tiff'
        ds = gdal.Open(f)
        ds = gdal.Translate(output_path, ds, options=['-of', 'GTiff'])
        ds = None
        src = rasterio.open(output_path, 'r')

    transform, width, height = calculate_default_transform(
        src.crs, dst_crs, src.width, src.height, *src.bounds
    )
    kwargs = src.meta.copy()
    kwargs.update({'crs': dst_crs, 'transform': transform, 'width': width, 'height': height})

    path = os.path.join(tmpdir, os.path.basename(src.name))
    with rasterio.open(path, 'w', **kwargs) as dst:
        for i in range(1, src.count + 1):
            reproject(
                source=rasterio.band(src, i),
                destination=rasterio.band(dst, i),
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=transform,
                dst_crs=dst_crs,
                resampling=Resampling.nearest,
            )
        dst.colorinterp = src.colorinterp
    return rasterio.open(path, 'r')


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
        # band_meta.creator = ife.creator
        # band_meta.modifier = ife.modifier
        try:
            band_meta.dtype = dtypes[i]
        except IndexError:
            pass
        bmin, bmax, mean, std = gdal_band.GetStatistics(True, True)
        band_meta.min = bmin
        band_meta.max = bmax
        band_meta.mean = mean
        band_meta.std = std

        try:
            band_meta.interpretation = interps[i].name
        except IndexError:
            pass

        # Save this band entirely
        band_meta.save()
    return


def read_image_file(ife):
    """Image ingestion routine.

    This helper will open an image file from ``ImageFile`` and create a
    ``ImageEntry`` and collection of ``BandMetaEntry`` entries.

    """
    # Fetch the image file this Layer corresponds to
    if not isinstance(ife, ImageFile):
        ife = ImageFile.objects.get(id=ife)

    with ife.file.yield_local_path() as file_path:
        logger.info(f'The image file path: {file_path}')

        image_entry, created = get_or_create_no_commit(
            ImageEntry, defaults=dict(name=ife.file.name), image_file=ife
        )
        if not created:
            # Clear out associated entries because they could be invalid
            BandMetaEntry.objects.filter(parent_image=image_entry).delete()
            ConvertedImageFile.objects.filter(source_image=image_entry).delete()

        _read_image_to_entry(image_entry, file_path)

    return image_entry


def create_image_entry_thumbnail(image_entry):
    # Fetch the image file this Layer corresponds to
    if not isinstance(image_entry, ImageEntry):
        image_entry = ImageEntry.objects.get(id=image_entry)

    thumbnail, created = get_or_create_no_commit(Thumbnail, image_entry=image_entry)

    with image_entry.image_file.file.yield_local_path() as file_path:
        logger.info(f'The image file path: {file_path}')
        with rasterio.open(file_path) as src:
            if src.crs:
                rsrc = _reproject_raster(src, WEB_MERCATOR)
                thumb_image = _create_thumbnail_image(rsrc)
            else:
                thumb_image = _create_thumbnail_image(src)

    thumbnail.base_thumbnail.save(f'{image_entry.image_file.file.name}.jpg', thumb_image, save=True)
    thumbnail.save()

    return image_entry


def _extract_raster_outline_fast(src):
    dst_crs = rasterio.crs.CRS.from_epsg(DB_SRID)
    left, bottom, right, top = transform_bounds(
        src.crs, dst_crs, src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top
    )
    coords = np.array(
        (
            (left, top),
            (right, top),
            (right, bottom),
            (left, bottom),
            (left, top),  # Close the loop
        )
    )
    return Polygon(coords, srid=DB_SRID)


def _extract_raster_meta(image_file_entry):
    """Extract all of the raster meta info in our models from an image file.

    The keys of the returned dict should match the fields of the
    ``RasterEntry``.

    """
    raster_meta = dict()
    with image_file_entry.file.yield_local_path() as path:
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
            raster_meta['outline'] = _extract_raster_outline_fast(src)
            raster_meta['footprint'] = raster_meta['outline']
    return raster_meta


def _get_valid_data_footprint(src, band_num):
    """Get ``GEOSGeometry`` of valid data footprint from the raster mask."""
    # Determine mask resolution to prevent loading massive imagery
    # shape = tuple(np.min([src.shape, MAX_LOAD_SHAPE], axis=0))
    # mask = src.read_masks(band_num, out_shape=shape, resampling=5)
    # TODO: fix transform to match this resampling
    mask = src.dataset_mask()

    # Extract feature shapes and values from the array.
    # Assumes already working in correct spatial reference
    for geom, val in rasterio.features.shapes(mask, transform=src.transform):
        # Ignore the 0-feature and only return on valid data feature
        if val:
            return GEOSGeometry(json.dumps(geom))

    raise ValueError('No valid raster footprint found.')


def _extract_raster_footprint(image_file_entry):
    """Extract the footprint of raster's image file entry.

    This operates on the assumption that the image file is a valid raster.

    """
    with image_file_entry.file.yield_local_path() as file_path:
        # Reproject the raster to the DB SRID using rasterio directly rather
        #  than transforming the extracted geometry which had issues.
        src = _reproject_raster(rasterio.open(file_path), DB_SRID)
        try:
            # Only implement for first band for now
            footprint = _get_valid_data_footprint(src, 1)
        except Exception as e:  # TODO: be more clever about this
            logger.info(f'Issue computing valid data footprint: {e}')
            footprint = None
    return footprint


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

    Will check if all have the same spatial reference/geo meta info.

    A ``ValueError`` will be raised if the image set cannot be evaluated as a
    single raster.

    Returns the meta info if it checks out.

    """
    images = list(image_set_entry.images.all())

    if not images:
        raise ValueError('ImageSet returned no images.')

    base_image = images.pop()
    last_meta = _extract_raster_meta(base_image.image_file.imagefile)
    for image in images:
        meta = _extract_raster_meta(image.image_file.imagefile)
        if not _compare_raster_meta(last_meta, meta):
            raise ValueError('Raster meta mismatch at image: {}'.format(image))
        last_meta = meta

    return last_meta


def populate_raster_entry(raster_id):
    """Autopopulate the fields of the raster."""
    raster_entry = RasterEntry.objects.get(id=raster_id)

    # Has potential to error with failure reason
    meta = _validate_image_set_is_raster(raster_entry.image_set)
    if not raster_entry.name:
        raster_entry.name = raster_entry.image_set.name
        raster_entry.save(
            update_fields=[
                'name',
            ]
        )
    footprint = meta.pop('footprint')
    raster_meta, created = get_or_create_no_commit(RasterMetaEntry, parent_raster=raster_entry)
    # Not using `defaults` here because we want `meta` to always get updated.
    for k, v in meta.items():
        # Yeah. This is sketchy, but it works.
        setattr(raster_meta, k, v)
    if not raster_meta.footprint:
        # Only set if not already set since this func defaults it to using outline
        raster_meta.footprint = footprint
    raster_meta.save()
    return True


def populate_raster_footprint(raster_id):
    raster_entry = RasterEntry.objects.get(id=raster_id)
    # Only set the footprint if the RasterMetaEntry has been created already
    #   this avoids a race condition where footprint might not get set correctly.
    try:
        raster_meta = RasterMetaEntry.objects.get(parent_raster=raster_entry)
    except RasterMetaEntry.DoesNotExist:
        logger.error('Cannot populate raster footprint yet due to race condition. Try again later.')
        return
    base_image = raster_entry.image_set.images.first()
    footprint = _extract_raster_footprint(base_image.image_file.imagefile)
    if footprint:
        raster_meta.footprint = footprint
        raster_meta.save(update_fields=['footprint'])
    return


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
    return


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
    tmpdir = tempfile.mkdtemp(dir=workdir)

    if ds_entry.image_set:
        # Delete all previously existing data
        # This should cascade to all the annotations
        for imageentry in ds_entry.image_set.images.all():
            imageentry.image_file.delete()
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
            image_file.skip_task = True
            image_file.file = ChecksumFile()
            image_file.file.file.save(name, open(image_file_abs_path, 'rb'))
            image_file.save()
            # Create a new ImageEntry
            image_entry = read_image_file(image_file)
            create_image_entry_thumbnail(image_entry)
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
    return
