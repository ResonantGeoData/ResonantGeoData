"""Tasks for subsampling images with GDAL."""
import os
import tempfile

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from girder_utils.files import field_file_to_local_path
from osgeo import gdal

from ..common import ArbitraryFile
from .base import ConvertedImageFile, SubsampledImage

logger = get_task_logger(__name__)


def _gdal_translate(source_field, output_field, **kwargs):
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    tmpdir = tempfile.mkdtemp(dir=workdir)

    with field_file_to_local_path(source_field) as file_path:
        logger.info(f'The image file path: {file_path}')
        output_path = os.path.join(tmpdir, 'subsampled_' + os.path.basename(file_path))
        ds = gdal.Open(str(file_path))
        ds = gdal.Translate(output_path, ds, **kwargs)
        ds = None

    output_field.save(os.path.basename(output_path), open(output_path, 'rb'))

    return


def convert_to_cog(cog):
    """Populate ConvertedImageFile with COG file."""
    options = [
        '-co',
        'COMPRESS=LZW',
        '-co',
        'TILED=YES',
    ]
    if not isinstance(cog, ConvertedImageFile):
        cog = ConvertedImageFile.objects.get(id=cog)
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
    return cog.id


def populate_subsampled_image(subsampled_id):
    sub = SubsampledImage.objects.get(id=subsampled_id)
    image_entry = sub.source_image

    # If COG of source isn't available, create it.
    try:
        cog = image_entry.convertedimagefile
    except ObjectDoesNotExist:
        cog = ConvertedImageFile()
        cog.source_image = image_entry
        cog.skip_signal = True  # Run conversion synchronously
        cog.save()
        convert_to_cog(cog)

    # Create kwargs based on subsample type
    kwargs = dict()
    if sub.sample_type == SubsampledImage.SampleTypes.GEO_BOX:
        # -projwin ulx uly lrx lry
        # kwargs = dict(projWin=[xmin, ymax, xmax, ymin])
        logger.info(f'sample params: {sub.sample_parameters}')
    elif sub.sample_type == SubsampledImage.SampleTypes.PIXEL_BOX:
        # -srcwin <xoff> <yoff> <xsize> <ysize>
        # kwargs = dict(srcWin=[umin, vmin, umax - umin, vmax - vmin])
        logger.info(f'sample params: {sub.sample_parameters}')
    elif sub.sample_type == SubsampledImage.SampleTypes.GEOJSON:
        raise NotImplementedError()
    else:
        raise ValueError('Sample type ({}) unknown.'.format(sub.sample_type))

    source_field = cog.converted_file.file
    if not sub.data:
        sub.data = ArbitraryFile()
    _gdal_translate(source_field, sub.data.file, **kwargs)
    sub.data.save()
    sub.save(
        update_fields=[
            'data',
        ]
    )
    return sub.id
