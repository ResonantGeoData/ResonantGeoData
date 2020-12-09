"""Tasks for subsampling images with GDAL."""
import os
import tempfile

from celery.utils.log import get_task_logger
from django.conf import settings
from osgeo import gdal

from rgd.utility import _field_file_to_local_path

from ..common import ArbitraryFile
from .base import ConvertedImageFile

logger = get_task_logger(__name__)


def _gdal_translate(source_field, output_field, **kwargs):
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    tmpdir = tempfile.mkdtemp(dir=workdir)

    with _field_file_to_local_path(source_field) as file_path:
        logger.info(f'The image file path: {file_path}')
        output_path = os.path.join(tmpdir, 'subsampled_' + os.path.basename(file_path))
        ds = gdal.Open(str(file_path))
        ds = gdal.Translate(output_path, ds, **kwargs)
        ds = None

    output_field.save(os.path.basename(output_path), open(output_path, 'rb'))

    return


def convert_to_cog(cog_id):
    """Populate ConvertedImageFile with COG file."""
    options = [
        '-co',
        'COMPRESS=LZW',
        '-co',
        'TILED=YES',
    ]
    cog = ConvertedImageFile.objects.get(id=cog_id)
    cog.converted_file = ArbitraryFile()
    src = cog.source_image.image_file.imagefile.file
    output = cog.converted_file.file
    _gdal_translate(src, output, options=options)
    cog.converted_file.save()
    cog.save(
        update_fields=[
            'converted_file',
        ]
    )
    return
