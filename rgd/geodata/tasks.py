import traceback

from celery import shared_task
from celery.utils.log import get_task_logger

# NOTE: do not import `models` to avoid recursive imports

logger = get_task_logger(__name__)


def _safe_execution(func, *args, **kwargs):
    """Execute a task and raturn any tracebacks that occur as a string."""
    tb = ''
    try:
        func(*args, **kwargs)
    except Exception as exc:
        logger.exception(f'Internal error run `{func.__name__}`: {exc}')
        tb = traceback.format_exc()
    return tb


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
    return


@shared_task(time_limit=86400)
def task_read_image_file(file_id):
    from .models.imagery.etl import populate_image_entry
    from .models.imagery.ifiles import ImageFile

    image_file = ImageFile.objects.get(id=file_id)
    _run_with_failure_reason(image_file, populate_image_entry, file_id)
    return


@shared_task(time_limit=86400)
def task_read_geometry_archive(archive_id):
    from .models.geometry.etl import GeometryArchive, read_geometry_archive

    archive = GeometryArchive.objects.get(id=archive_id)
    _run_with_failure_reason(archive, read_geometry_archive, archive_id)
    return


@shared_task(time_limit=86400)
def task_populate_raster_entry(raster_id):
    from .models.imagery.base import RasterEntry
    from .models.imagery.etl import populate_raster_entry

    raster_entry = RasterEntry.objects.get(id=raster_id)
    _run_with_failure_reason(raster_entry, populate_raster_entry, raster_id)
    return


@shared_task(time_limit=86400)
def task_load_kwcoco_dataset(kwcoco_dataset_id):
    logger.exception('running task_load_kwcoco_dataset')
    from .models.imagery.base import KWCOCOArchive
    from .models.imagery.etl import load_kwcoco_dataset

    ds_entry = KWCOCOArchive.objects.get(id=kwcoco_dataset_id)
    _run_with_failure_reason(ds_entry, load_kwcoco_dataset, kwcoco_dataset_id)
    return


@shared_task(time_limit=86400)
def task_read_fmv_file(file_id):
    from .models.fmv.base import FMVFile
    from .models.fmv.etl import read_fmv_file

    fmv_file = FMVFile.objects.get(id=file_id)
    _run_with_failure_reason(fmv_file, read_fmv_file, file_id)
    return
