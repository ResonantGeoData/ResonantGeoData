"""Tasks for subsampling images with GDAL."""
from contextlib import contextmanager

from celery.utils.log import get_task_logger
from django.contrib.gis.geos import GEOSGeometry
import large_image_converter
import rasterio
from rasterio.merge import merge
from rasterio.warp import Resampling
from rgd.models import ChecksumFile
from rgd.utility import input_output_path_helper, output_path_helper
from rgd_imagery import large_image_utilities
from rgd_imagery.models import Annotation, Image, ProcessedImage, ProcessedImageGroup
from shapely.geometry import shape
from shapely.wkb import dumps

logger = get_task_logger(__name__)


@contextmanager
def _processed_image_helper(param_model, single_input=False):
    # yields the source image object and the processed image file object
    if param_model.processed_image:
        param_model.processed_image.file.delete()
    file = ChecksumFile()

    param_model.refresh_from_db()

    if single_input:
        if param_model.source_images.count() != 1:
            raise RuntimeError(
                f'There must be one and only one source image. {param_model.source_images.count()} were given.'
            )
        yield (param_model.source_images.first(), file)
    else:
        yield (param_model.source_images.all(), file)

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


def convert_to_cog(param_model):
    """Convert Image to Cloud Optimized GeoTIFF."""
    with _processed_image_helper(param_model, single_input=True) as (image, output):

        with input_output_path_helper(image.file, output.file, prefix='cog_', vsi=True) as (
            input_path,
            output_path,
        ):
            large_image_converter.convert(str(input_path), str(output_path))


def extract_region(processed_image):
    parameters = processed_image.group.parameters
    sample_type = parameters['sample_type']
    logger.info(f'Subsample parameters: {parameters}')

    class SampleTypes:
        PIXEL_BOX = 'pixel box'
        GEO_BOX = 'geographic box'
        GEOJSON = 'geojson'
        ANNOTATION = 'annotation'

    def get_extent():
        """Convert ``parameters`` to length 4 tuple of XY extents.

        Note
        ----
        A ``KeyError`` could be raised if the sample parameters are illformed.

        Return
        ------
        extents, projection: <left, right, bottom, top>, <projection>

        """
        p = parameters

        projection = p.pop('projection', None)
        if sample_type in (
            SampleTypes.PIXEL_BOX,
            SampleTypes.ANNOTATION,
        ):
            projection = 'pixels'

        if sample_type in (
            SampleTypes.GEO_BOX,
            SampleTypes.PIXEL_BOX,
        ):
            return p['left'], p['right'], p['bottom'], p['top'], projection
        elif sample_type == SampleTypes.GEOJSON:
            # Convert GeoJSON to extents
            geom = shape(p)
            feature = GEOSGeometry(memoryview(dumps(geom)))
            l, b, r, t = feature.extent  # (xmin, ymin, xmax, ymax)
            return l, r, b, t, projection
        elif sample_type == SampleTypes.ANNOTATION:
            ann_id = p['id']
            ann = Annotation.objects.get(id=ann_id)
            l, b, r, t = ann.segmentation.outline.extent  # (xmin, ymin, xmax, ymax)
            return l, r, b, t, projection
        else:
            raise ValueError('Sample type ({}) unknown.'.format(sample_type))

    l, r, b, t, projection = get_extent()

    with _processed_image_helper(processed_image, single_input=True) as (image, output):
        tile_source = large_image_utilities.get_tilesource_from_image(image)

        filename = f'region-{image.file.name}'

        with output_path_helper(filename, output.file) as output_path:
            logger.info(f'The extent: {l, r, b, t}')
            if sample_type in (
                SampleTypes.GEOJSON,
                SampleTypes.GEO_BOX,
            ):
                path, mime_type = large_image_utilities.get_region_world(
                    tile_source, l, r, b, t, projection=projection
                )
            else:
                path, mime_type = large_image_utilities.get_region_pixel(tile_source, l, r, b, t)
            with open(path, 'rb') as f, open(output_path, 'wb') as o:
                o.write(f.read())


def resample_image(processed_image):

    factor = float(processed_image.group.parameters['sample_factor'])
    logger.info(f'Resample factor: {factor}')

    with _processed_image_helper(processed_image, single_input=True) as (image, output):

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


def mosaic_images(processed_image):
    with _processed_image_helper(processed_image) as (images, output):

        src_files_to_mosaic = []
        for image in images:
            file_path = image.file.get_vsi_path(internal=True)
            src_files_to_mosaic.append(rasterio.open(file_path))

        with output_path_helper('mosaic.tif', output.file) as output_path:
            mosaic, out_trans = merge(src_files_to_mosaic)
            out_meta = src_files_to_mosaic[0].meta.copy()

            # Update the metadata
            out_meta.update(
                {
                    'driver': 'GTiff',
                    'height': mosaic.shape[1],
                    'width': mosaic.shape[2],
                    'transform': out_trans,
                }
            )

            with rasterio.open(output_path, 'w', **out_meta) as dest:
                dest.write(mosaic)


def run_processed_image(processed_image):
    if not isinstance(processed_image, ProcessedImage):
        processed_image = ProcessedImage.objects.get(id=processed_image)

    methods = {
        ProcessedImageGroup.ProcessTypes.COG: convert_to_cog,
        ProcessedImageGroup.ProcessTypes.REGION: extract_region,
        ProcessedImageGroup.ProcessTypes.RESAMPLE: resample_image,
        ProcessedImageGroup.ProcessTypes.ARBITRARY: lambda *args: None,
        ProcessedImageGroup.ProcessTypes.MOSAIC: mosaic_images,
    }
    return methods[processed_image.group.process_type](processed_image)
