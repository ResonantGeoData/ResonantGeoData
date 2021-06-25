"""Tasks for subsampling images with GDAL."""
from contextlib import contextmanager

from celery.utils.log import get_task_logger
import large_image_converter
from rgd.models import ChecksumFile
from rgd.utility import input_output_path_helper, output_path_helper
from rgd_imagery import large_image_utilities
from rgd_imagery.models import ConvertedImage, Image, RegionImage

logger = get_task_logger(__name__)


@contextmanager
def _processed_image_helper(param_model):
    # yields the source image object and the processed image file object
    if not param_model.processed_image:
        file = ChecksumFile()
    else:
        file = param_model.processed_image.file

    yield (param_model.source_image, file)

    file.save()

    if not param_model.processed_image:
        param_model.processed_image = Image()
    param_model.processed_image.file = file
    param_model.processed_image.save()
    param_model.save(
        update_fields=[
            'processed_image',
        ]
    )
    logger.info(f'Produced ProcessedImage in ChecksumFile: {param_model.processed_image.file.id}')


def convert_to_cog(cog):
    """Populate ConvertedImage with COG file."""
    if not isinstance(cog, ConvertedImage):
        cog = ConvertedImage.objects.get(id=cog)
    else:
        cog.refresh_from_db()

    with _processed_image_helper(cog) as (image, output):

        with input_output_path_helper(image.file, output.file, prefix='cog_', vsi=True) as (
            input_path,
            output_path,
        ):
            large_image_converter.convert(str(input_path), str(output_path))


def populate_region_image(region):
    if not isinstance(region, RegionImage):
        region = RegionImage.objects.get(id=region)
    else:
        region.refresh_from_db()

    logger.info(f'Subsample parameters: {region.sample_parameters}')
    l, r, b, t, projection = region.get_extent()

    with _processed_image_helper(region) as (image, output):
        tile_source = large_image_utilities.get_tilesource_from_image(image)

        filename = f'region-{image.file.name}'

        with output_path_helper(filename, output.file) as output_path:
            logger.info(f'The extent: {l, r, b, t}')
            if region.sample_type in (
                RegionImage.SampleTypes.GEOJSON,
                RegionImage.SampleTypes.GEO_BOX,
            ):
                path, mime_type = large_image_utilities.get_region_world(
                    tile_source, l, r, b, t, projection=projection
                )
            else:
                path, mime_type = large_image_utilities.get_region_pixel(tile_source, l, r, b, t)
            with open(path, 'rb') as f, open(output_path, 'wb') as o:
                o.write(f.read())
