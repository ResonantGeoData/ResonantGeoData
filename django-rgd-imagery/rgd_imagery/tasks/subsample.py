"""Tasks for subsampling images with GDAL."""
from contextlib import contextmanager

from celery.utils.log import get_task_logger
import large_image_converter
import rasterio
from rasterio.warp import Resampling
from rgd.models import ChecksumFile
from rgd.utility import input_output_path_helper, output_path_helper
from rgd_imagery import large_image_utilities
from rgd_imagery.models import ConvertedImage, Image, RegionImage, ResampledImage

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

    if param_model.add_to_sets:
        for imset in param_model.source_image.imageset_set.all():
            imset.images.add(param_model.processed_image)


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


def resample_image(resample):
    if not isinstance(resample, ResampledImage):
        resample = ResampledImage.objects.get(id=resample)
    else:
        resample.refresh_from_db()

    factor = resample.sample_factor
    logger.info(f'Resample factor: {factor}')

    with _processed_image_helper(resample) as (image, output):

        with input_output_path_helper(
            image.file, output.file, prefix='resampled_{:.2f}_'.format(factor), vsi=True
        ) as (
            input_path,
            output_path,
        ):

            with rasterio.open(input_path) as dataset:

                # resample data to target shape
                data = dataset.read(
                    out_shape=(
                        dataset.count,
                        int(dataset.height * factor),
                        int(dataset.width * factor),
                    ),
                    resampling=Resampling.bilinear,
                )

                # scale image transform
                transform = dataset.transform * dataset.transform.scale(
                    (dataset.width / data.shape[-1]), (dataset.height / data.shape[-2])
                )

                out_meta = dataset.meta.copy()

                # Update the metadata
                out_meta.update(
                    {
                        'driver': 'GTiff',
                        'height': data.shape[1],
                        'width': data.shape[2],
                        'transform': transform,
                    }
                )

                with rasterio.open(output_path, 'w', **out_meta) as dest:
                    dest.write(data)
