import traceback

from celery import shared_task
from celery.utils.log import get_task_logger

# NOTE: do not import `models` to avoid recursive imports

logger = get_task_logger(__name__)


def _safe_execution(func, *args, **kwargs):
    """Execute a task and return any tracebacks that occur as a string."""
    try:
        func(*args, **kwargs)
        return ''
    except Exception as exc:
        logger.exception(f'Internal error run `{func.__name__}`: {exc}')
        return traceback.format_exc()


def _run_with_failure_reason(model, func, *args, **kwargs):
    """Run a function that will update the model's `failure_reason`."""
    from .models.mixins import Status

    model.status = Status.RUNNING
    model.save(update_fields=['status'])
    model.failure_reason = _safe_execution(func, *args, **kwargs)
    if model.failure_reason:
        model.status = Status.FAILED
    else:
        model.status = Status.SUCCEEDED
    model.save(update_fields=['failure_reason', 'status'])


@shared_task(time_limit=86400)
def task_read_image_file(file_id):
    from .models.imagery.base import ImageFile
    from .models.imagery.etl import read_image_file

    image_file = ImageFile.objects.get(id=file_id)
    _run_with_failure_reason(image_file, read_image_file, file_id)


@shared_task(time_limit=86400)
def task_read_geometry_archive(archive_id):
    from .models.geometry.etl import GeometryArchive, read_geometry_archive

    archive = GeometryArchive.objects.get(id=archive_id)
    _run_with_failure_reason(archive, read_geometry_archive, archive_id)


@shared_task(time_limit=86400)
def task_populate_raster_entry(raster_id):
    from .models.imagery.base import RasterEntry
    from .models.imagery.etl import populate_raster_entry

    raster_entry = RasterEntry.objects.get(id=raster_id)
    _run_with_failure_reason(raster_entry, populate_raster_entry, raster_id)


@shared_task(time_limit=86400)
def task_populate_raster_footprint(raster_id):
    from .models.imagery.base import RasterEntry
    from .models.imagery.etl import populate_raster_footprint

    raster_entry = RasterEntry.objects.get(id=raster_id)
    _run_with_failure_reason(raster_entry, populate_raster_footprint, raster_id)


@shared_task(time_limit=86400)
def task_populate_raster_outline(raster_id):
    from .models.imagery.base import RasterEntry
    from .models.imagery.etl import populate_raster_outline

    raster_entry = RasterEntry.objects.get(id=raster_id)
    _run_with_failure_reason(raster_entry, populate_raster_outline, raster_id)


@shared_task(time_limit=86400)
def task_load_kwcoco_dataset(kwcoco_dataset_id):
    from .models.imagery.base import KWCOCOArchive
    from .models.imagery.etl import load_kwcoco_dataset

    ds_entry = KWCOCOArchive.objects.get(id=kwcoco_dataset_id)
    _run_with_failure_reason(ds_entry, load_kwcoco_dataset, kwcoco_dataset_id)


@shared_task(time_limit=86400)
def task_read_fmv_file(file_id):
    from .models.fmv.base import FMVFile
    from .models.fmv.etl import read_fmv_file

    fmv_file = FMVFile.objects.get(id=file_id)
    _run_with_failure_reason(fmv_file, read_fmv_file, file_id)


@shared_task(time_limit=86400)
def task_convert_to_cog(conv_id):
    from .models.imagery.base import ConvertedImageFile
    from .models.imagery.subsample import convert_to_cog

    cog = ConvertedImageFile.objects.get(id=conv_id)
    _run_with_failure_reason(cog, convert_to_cog, conv_id)


@shared_task(time_limit=86400)
def task_populate_subsampled_image(subsampled_id):
    from .models.imagery.base import SubsampledImage
    from .models.imagery.subsample import populate_subsampled_image

    cog = SubsampledImage.objects.get(id=subsampled_id)
    _run_with_failure_reason(cog, populate_subsampled_image, subsampled_id)


@shared_task(time_limit=86400)
def task_checksum_file_post_save(checksumfile_id):
    from .models.common import ChecksumFile

    obj = ChecksumFile.objects.get(id=checksumfile_id)

    _run_with_failure_reason(obj, obj.post_save_job)
