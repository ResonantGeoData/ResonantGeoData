"""Tasks for subsampling images with GDAL."""
from contextlib import contextmanager
import os
import tempfile

from celery.utils.log import get_task_logger
from django.conf import settings
import large_image_converter
from osgeo import gdal
import rasterio
from rasterio.mask import mask

from rgd.utility import get_or_create_no_commit

from ..common import ChecksumFile
from .base import ConvertedImageFile, SubsampledImage

logger = get_task_logger(__name__)


@contextmanager
def _input_output_path_helper(source, output, prefix=''):
    """Yeild source and output paths between to FileFeilds.

    The output is saved to the output field after yeilding.

    """
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
        with source.yield_local_path() as file_path:
            output_path = os.path.join(tmpdir, prefix + os.path.basename(source.name))
            yield (file_path, output_path)

        with open(output_path, 'rb') as f:
            output.save(os.path.basename(output_path), f)


def _gdal_translate_helper(source, output, prefix='', **kwargs):
    with _input_output_path_helper(source, output, prefix=prefix) as (input_path, output_path):
        ds = gdal.Open(str(input_path))
        ds = gdal.Translate(str(output_path), ds, **kwargs)
        ds = None


def convert_to_cog(cog):
    """Populate ConvertedImageFile with COG file."""
    if not isinstance(cog, ConvertedImageFile):
        cog = ConvertedImageFile.objects.get(id=cog)
    else:
        cog.refresh_from_db()
    if not cog.converted_file:
        cog.converted_file = ChecksumFile()
    src = cog.source_image.image_file.imagefile.file
    output = cog.converted_file.file

    with _input_output_path_helper(src, output, prefix='cog_') as (input_path, output_path):
        large_image_converter.convert(str(input_path), str(output_path))

    cog.converted_file.save()
    cog.save(
        update_fields=[
            'converted_file',
        ]
    )
    logger.info(f'Produced COG in ChecksumFile: {cog.converted_file.id}')
    return cog.id


def _subsample_with_geojson(source, output, geojson, prefix=''):
    with _input_output_path_helper(source, output, prefix=prefix) as (input_path, output_path):
        # load the raster, mask it by the polygon and crop it
        with rasterio.open(input_path) as src:
            out_image, out_transform = mask(src, [geojson], crop=True)
            out_meta = src.meta.copy()
            driver = src.driver

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

    source = cog.converted_file
    if not subsampled.data:
        subsampled.data = ChecksumFile()

    if subsampled.sample_type == SubsampledImage.SampleTypes.GEOJSON or (
        subsampled.sample_type == SubsampledImage.SampleTypes.ANNOTATION
        and kwargs.get('type', None)
    ):
        logger.info('Subsampling with GeoJSON feature.')
        _subsample_with_geojson(source, subsampled.data.file, kwargs, prefix='subsampled_')
    else:
        logger.info('Subsampling with bounding box feature.')
        _gdal_translate_helper(source, subsampled.data.file, prefix='subsampled_', **kwargs)

    subsampled.data.save()
    subsampled.save(
        update_fields=[
            'data',
        ]
    )
    logger.info(f'Produced subsampled image in ChecksumFile: {subsampled.data.id}')
    return subsampled.id
