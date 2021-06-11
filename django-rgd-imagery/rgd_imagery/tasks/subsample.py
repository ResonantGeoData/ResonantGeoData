"""Tasks for subsampling images with GDAL."""
from celery.utils.log import get_task_logger
import large_image_converter

from rgd.utility import input_output_path_helper, output_path_helper

from . import large_image_utilities
from ..common import ChecksumFile
from .processed import ConvertedImageFile, SubsampledImage

logger = get_task_logger(__name__)


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

    with input_output_path_helper(src, output, prefix='cog_', vsi=True) as (
        input_path,
        output_path,
    ):
        large_image_converter.convert(str(input_path), str(output_path))

    cog.save(
        update_fields=[
            'converted_file',
        ]
    )
    logger.info(f'Produced COG in ChecksumFile: {cog.converted_file.id}')
    return cog.id


def populate_subsampled_image(subsampled):
    if not isinstance(subsampled, SubsampledImage):
        subsampled = SubsampledImage.objects.get(id=subsampled)
    else:
        subsampled.refresh_from_db()
    image_entry = subsampled.source_image

    logger.info(f'Subsample parameters: {subsampled.sample_parameters}')
    l, r, b, t, projection = subsampled.get_extent()

    if not subsampled.data:
        subsampled.data = ChecksumFile()

    tile_source = large_image_utilities.get_tilesource_from_image_entry(image_entry)

    filename = f'subsampled-{image_entry.image_file.file.name}'

    with output_path_helper(filename, subsampled.data.file) as output_path:
        logger.info(f'The extent: {l, r, b, t}')
        if subsampled.sample_type in (
            SubsampledImage.SampleTypes.GEOJSON,
            SubsampledImage.SampleTypes.GEO_BOX,
        ):
            path, mime_type = large_image_utilities.get_region_world(
                tile_source, l, r, b, t, projection=projection
            )
        else:
            path, mime_type = large_image_utilities.get_region_pixel(tile_source, l, r, b, t)
        with open(path, 'rb') as f, open(output_path, 'wb') as o:
            o.write(f.read())

    subsampled.data.save()
    subsampled.save(
        update_fields=[
            'data',
        ]
    )
    logger.info(f'Produced subsampled image in ChecksumFile: {subsampled.data.id}')
    return subsampled.id
