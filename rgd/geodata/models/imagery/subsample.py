"""Tasks for subsampling images with GDAL."""
import os
import tempfile

from celery.utils.log import get_task_logger
from django.conf import settings
from girder_utils.files import field_file_to_local_path
from osgeo import gdal
import rasterio
from rasterio.mask import mask

from rgd.utility import get_or_create_no_commit

from ..common import ArbitraryFile
from .base import ConvertedImageFile, SubsampledImage

logger = get_task_logger(__name__)


COG_OPTIONS = [
    '-co',
    'COMPRESS=LZW',
    '-co',
    'PREDICTOR=YES',
    '-of',
    'COG',
    '-co',
    'BLOCKSIZE=256',
]


def _gdal_translate(src_path, dest_path, **kwargs):
    ds = gdal.Open(str(src_path))
    ds = gdal.Translate(str(dest_path), ds, **kwargs)
    ds = None
    return dest_path


def _gdal_translate_fields(source_field, output_field, prefix='', **kwargs):
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    tmpdir = tempfile.mkdtemp(dir=workdir)

    with field_file_to_local_path(source_field) as file_path:
        logger.info(f'The image file path: {file_path}')
        output_path = os.path.join(tmpdir, prefix + os.path.basename(source_field.name))
        _gdal_translate(file_path, output_path, **kwargs)

    output_field.save(os.path.basename(output_path), open(output_path, 'rb'))

    return


def convert_to_cog(cog):
    """Populate ConvertedImageFile with COG file."""
    if not isinstance(cog, ConvertedImageFile):
        cog = ConvertedImageFile.objects.get(id=cog)
    else:
        cog.refresh_from_db()
    if not cog.converted_file:
        cog.converted_file = ArbitraryFile()
    src = cog.source_image.image_file.imagefile.file
    output = cog.converted_file.file
    _gdal_translate_fields(src, output, prefix='cog_', options=COG_OPTIONS)
    cog.converted_file.save()
    cog.save(
        update_fields=[
            'converted_file',
        ]
    )
    logger.info(f'Produced COG in ArbitraryFile: {cog.converted_file.id}')
    return cog.id


def _subsample_with_geojson(source_field, output_field, geojson, prefix=''):
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    tmpdir = tempfile.mkdtemp(dir=workdir)

    with field_file_to_local_path(source_field) as file_path:
        # load the raster, mask it by the polygon and crop it
        with rasterio.open(file_path) as src:
            out_image, out_transform = mask(src, [geojson], crop=True)
            out_meta = src.meta.copy()
            driver = src.driver

        output_path = os.path.join(tmpdir, prefix + os.path.basename(source_field.name))

    # save the resulting raster
    out_meta.update(
        {
            'driver': driver,
            'height': out_image.shape[1],
            'width': out_image.shape[2],
            'transform': out_transform,
        }
    )

    with rasterio.open(output_path, 'w', **out_meta) as dest:
        dest.write(out_image)

    # Convert subsampled to COG
    # NOTE: this cannot subsampling produce a COG because it is irregular
    # _gdal_translate(output_path, output_path, options=COG_OPTIONS)
    output_field.save(os.path.basename(output_path), open(output_path, 'rb'))
    return


def populate_subsampled_image(subsampled):
    if not isinstance(subsampled, SubsampledImage):
        subsampled = SubsampledImage.objects.get(id=subsampled)
    else:
        subsampled.refresh_from_db()
    image_entry = subsampled.source_image

    cog, created = get_or_create_no_commit(ConvertedImageFile, source_image=image_entry)
    if created:
        cog.skip_signal = True  # Run conversion synchronously
        cog.save()
        convert_to_cog(cog)

    # Create kwargs based on subsample type
    logger.info(f'Subsample parameters: {subsampled.sample_parameters}')
    kwargs = subsampled.to_kwargs()

    source_field = cog.converted_file.file
    if not subsampled.data:
        subsampled.data = ArbitraryFile()

    if subsampled.sample_type == SubsampledImage.SampleTypes.GEOJSON or (
        subsampled.sample_type == SubsampledImage.SampleTypes.ANNOTATION
        and kwargs.get('type', None)
    ):
        logger.info('Subsampling with GeoJSON feature.')
        _subsample_with_geojson(source_field, subsampled.data.file, kwargs, prefix='subsampled_')
    else:
        logger.info('Subsampling with bounding box feature.')
        _gdal_translate_fields(source_field, subsampled.data.file, prefix='subsampled_', **kwargs)

    subsampled.data.save()
    subsampled.save(
        update_fields=[
            'data',
        ]
    )
    logger.info(f'Produced subsampled image in ArbitraryFile: {subsampled.data.id}')
    return subsampled.id
