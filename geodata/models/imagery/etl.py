"""Helper methods for creating a ``GDALRaster`` entry from a raster file."""
import os
import tempfile
import zipfile

from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import LineString, MultiPoint, MultiPolygon, Point, Polygon
import kwcoco
import kwimage
import numpy as np
from osgeo import gdal
import rasterio

from rgd.utility import _field_file_to_local_path

from ..geometry.transform import transform_geometry
from .annotation import Annotation, PolygonSegmentation, RLESegmentation, Segmentation
from .base import (
    BandMetaEntry,
    ConvertedImageFile,
    ImageEntry,
    ImageSet,
    KWCOCOArchive,
    RasterEntry,
)
from .ifiles import ImageArchiveFile, ImageFile

logger = get_task_logger(__name__)


MAX_LOAD_SHAPE = (4000, 4000)


# def create_thumbnail(src):
#     oview = int(max(src.height, src.width) * 0.1) or 1
#     thumbnail = src.read(1, out_shape=(1, int(src.height // oview), int(src.width // oview)))
#
#     buf = io.BytesIO()
#     thumbnail.save(buf, format='JPEG')
#     byte_im = buf.getvalue()
#     return ContentFile(byte_im)


def _read_image_to_entry(image_entry, image_file_path):

    with rasterio.open(image_file_path) as src:
        image_entry.number_of_bands = src.count
        image_entry.driver = src.driver
        image_entry.height = src.shape[0]
        image_entry.width = src.shape[1]

        # A catch-all metadata feild:
        # TODO: image_entry.metadata =

        # thumbnail = create_thumbnail(src)
        # image_entry.thumbnail.save('thumbnail.jpg', thumbnail, save=True)

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


def populate_image_entry(image_file_id):
    """Image ingestion routine.

    This helper will open an image file from ``ImageFile`` and create a
    ``ImageEntry`` and collection of ``BandMetaEntry`` entries.

    """
    # Fetch the raster file this Layer corresponds to
    ife = ImageFile.objects.get(id=image_file_id)
    with _field_file_to_local_path(ife.file) as file_path:

        logger.info(f'The image file path: {file_path}')

        image_query = ImageEntry.objects.filter(image_file=ife)
        if len(image_query) < 1:
            image_entry = ImageEntry()
            image_entry.name = ife.name
            # image_entry.creator = ife.creator
        elif len(image_query) == 1:
            image_entry = image_query.first()
            # Clear out associated entries because they could be invalid
            BandMetaEntry.objects.filter(parent_image=image_entry).delete()
            ConvertedImageFile.objects.filter(source_image=image_entry).delete()
        else:
            # This should never happen because it is a foreign key
            raise RuntimeError('multiple image entries found for this file.')  # pragma: no cover

        image_entry.image_file = ife
        # image_entry.modifier = ife.modifier
        _read_image_to_entry(image_entry, file_path)

    return True


def _extract_raster_meta(image_file_entry):
    """Extract all of the raster meta info in our models from an image file.

    The keys of the returned dict should match the fields of the
    ``RasterEntry``.

    """
    raster_meta = dict()
    with _field_file_to_local_path(image_file_entry.file) as file_path:
        with rasterio.open(file_path) as src:
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
    return raster_meta


def _convex_hull(points):
    from scipy.spatial import ConvexHull

    hull = ConvexHull(points)

    boundary = points[hull.vertices]
    # Close the loop
    boundary = np.append(boundary, boundary[0][None], axis=0)

    return boundary


def _get_valid_data_footprint(src, band_num):
    """Fetch points for the footprint polygon of the valid data.

    Must specify band of the raster to evaluate.

    src is an open dataset with rasterio

    Returns a numpy array of the bounadry points in a closed polygon.

    """
    # Determine mask resolution to prevent loading massive imagery
    shape = tuple(np.min([src.shape, MAX_LOAD_SHAPE], axis=0))

    msk = src.read_masks(band_num, out_shape=shape, resampling=5)

    # Figure out cell spacing from reduced size:
    da = (src.bounds.right - src.bounds.left) / msk.shape[1]
    db = (src.bounds.top - src.bounds.bottom) / msk.shape[0]

    a = (np.arange(msk.shape[1]) * da) + (src.bounds.left + (da / 2.0))
    b = (np.arange(msk.shape[0]) * db) + (src.bounds.bottom + (db / 2.0))
    xx, yy = np.meshgrid(a, b[::-1])
    ids = np.argwhere(msk.ravel()).ravel()

    x = xx.ravel()[ids]
    y = yy.ravel()[ids]
    points = np.c_[x, y]

    return _convex_hull(points)


def _extract_raster_outline_and_footprint(image_file_entry):
    """Extract the outline and footprint of raster's image file entry.

    This operates on the assumption that the image file is a valid raster.

    """
    with _field_file_to_local_path(image_file_entry.file) as file_path:
        # There is a potential conflict between rasterio and whatever GDAL
        # is available.  Rastio has an older form of GDAL and conflicts
        # with a system GDAL if the version is different.  So far, the only
        # issue seems to be with rastio's <source>.crs.  We can work around
        # this by using GDAL directly.
        gsrc = gdal.Open(str(file_path))
        spatial_ref_wkt = gsrc.GetSpatialRef().ExportToWkt()
        spatial_ref = SpatialReference(spatial_ref_wkt)

        with rasterio.open(file_path) as src:
            coords = np.array(
                (
                    (src.bounds.left, src.bounds.top),
                    (src.bounds.right, src.bounds.top),
                    (src.bounds.right, src.bounds.bottom),
                    (src.bounds.left, src.bounds.bottom),
                    (src.bounds.left, src.bounds.top),  # Close the loop
                )
            )

            logger.info(f'Raster footprint SRID: {spatial_ref.srid}')
            # This will convert the Polygon to the DB's SRID
            outline = transform_geometry(Polygon(coords, srid=spatial_ref.srid), spatial_ref_wkt)
            try:
                # Only implement for first band for now
                vcoords = _get_valid_data_footprint(src, 1)
                footprint = transform_geometry(
                    Polygon(vcoords, srid=spatial_ref.srid), spatial_ref_wkt
                )
            except Exception as e:  # TODO: be more clever about this
                logger.info(f'Issue computing convex hull of non-null data: {e}')
                footprint = outline

    return outline, footprint


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

    # Assume these are the same... only compute once
    outline, footprint = _extract_raster_outline_and_footprint(base_image.image_file.imagefile)
    last_meta['outline'] = outline
    last_meta['footprint'] = footprint

    return last_meta


def populate_raster_entry(raster_id):
    """Autopopulate the fields of the raster."""
    raster_entry = RasterEntry.objects.get(id=raster_id)

    try:
        meta = _validate_image_set_is_raster(raster_entry)
    except ValueError as err:
        raster_entry.failure_reason = str(err)
        raster_entry.save(update_fields=['failure_reason'])
        return False

    for k, v in meta.items():
        # Yeah. This is sketchy, but it works.
        setattr(raster_entry, k, v)

    raster_entry.save(update_fields=list(meta.keys()))
    return True


def _fill_annotation_segmentation(annotation_entry, ann_json):
    """For converting KWCOCO annotation JSON to an Annotation entry."""
    if 'keypoints' in ann_json:
        # populate keypoints - ignore 3rd value visibility
        points = np.array(ann_json['keypoints']).astype(float).reshape((-1, 3))
        keypoints = []
        for pt in points:
            logger.info(f'The Point: {pt}')
            keypoints.append(Point(pt[0], pt[1]))
        annotation_entry.keypoints = MultiPoint(*keypoints)
    if 'line' in ann_json:
        # populate line
        points = np.array(ann_json['line']).astype(float).reshape((-1, 2))
        logger.info(f'The line: {points}')
        annotation_entry.line = LineString(*[(pt[0], pt[1]) for pt in points], srid=0)
    # Add a segmentation
    segmentation = None
    if 'segmentation' in ann_json:
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
    if 'bbox' in ann_json:
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
    # Save if a segmentation is used
    if segmentation:
        segmentation.annotation = annotation_entry
        segmentation.save()
    return


def load_kwcoco_dataset(kwcoco_dataset_id):
    logger.info('Starting KWCOCO ETL routine')
    ds_entry = KWCOCOArchive.objects.get(id=kwcoco_dataset_id)
    ds_entry.failure_reason = ''

    # TODO: add a setting like this:
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    tmpdir = tempfile.mkdtemp(dir=workdir)

    if ds_entry.image_set:
        # Delete all previously existing data
        # This should cascade to all the annotations
        ds_entry.image_set.images.all().delete()
    else:
        ds_entry.image_set = ImageSet()
    ds_entry.image_set.name = ds_entry.name
    ds_entry.image_set.save()
    ds_entry.save(
        update_fields=[
            'image_set',
            'failure_reason',
        ]  # noqa: E231
    )

    # Unarchive the images locally so we can import them when loading the spec
    # Images could come from a URL, so this is optional
    if ds_entry.image_archive:
        with _field_file_to_local_path(ds_entry.image_archive.file) as file_path:
            logger.info(f'The KWCOCO image archive: {file_path}')
            # Place images in a local directory and keep track of root path
            # Unzip the contents to the working dir
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            logger.info(f'The extracted KWCOCO image archive: {tmpdir}')
    else:
        pass
        # TODO: how should we download data from specified URLs?

    # Load the KWCOCO JSON spec and make annotations on the images
    with _field_file_to_local_path(ds_entry.spec_file.file) as file_path:
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
            image_file = ImageArchiveFile()
            image_file.archive = ds_entry.image_archive
            image_file.path = img['file_name']
            image_file.save()
            # Create a new ImageEntry
            image_entry = ImageEntry()
            image_file_abs_path = os.path.join(ds.img_root, img['file_name'])
            _read_image_to_entry(image_entry, image_file_abs_path)
            image_entry.name = os.path.basename(image_file_abs_path)
            image_entry.image_file = image_file
            image_entry.save()
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
                annotation_entry.save()
                _fill_annotation_segmentation(annotation_entry, ann)
    logger.info('Done with KWCOCO ETL routine')
    return
