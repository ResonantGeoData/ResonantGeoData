from celery import shared_task
from celery.utils.log import get_task_logger

# NOTE: do not import `models` to avoid recursive imports

logger = get_task_logger(__name__)


@shared_task(time_limit=86400)
def task_read_image_file(file_id):
    from .models.imagery.etl import populate_image_entry
    from .models.imagery.ifiles import ImageFile

    image_file = ImageFile.objects.get(id=file_id)
    try:
        populate_image_entry(file_id)
        image_file.failure_reason = ''
    except Exception as exc:
        logger.exception(f'Internal error run `populate_image_entry`: {exc}')
        image_file.failure_reason = str(exc)
    image_file.save(update_fields=['failure_reason'])
    return


@shared_task(time_limit=86400)
def task_read_geometry_archive(archive_id):
    from .models.geometry.etl import GeometryArchive, read_geometry_archive

    archive = GeometryArchive.objects.get(id=archive_id)
    try:
        read_geometry_archive(archive_id)
        archive.failure_reason = ''
    except Exception as exc:
        logger.exception(f'Internal error run `read_geometry_archive`: {exc}')
        archive.failure_reason = str(exc)
    archive.save(update_fields=['failure_reason'])
    return


@shared_task(time_limit=86400)
def task_populate_raster_entry(raster_id):
    from .models.imagery.etl import populate_raster_entry

    try:
        populate_raster_entry(raster_id)
    except Exception as exc:
        logger.exception(f'Internal error run `populate_raster_entry`: {exc}')
    return


@shared_task(time_limit=86400)
def task_load_kwcoco_dataset(kwcoco_dataset_id):
    logger.exception('running task_load_kwcoco_dataset')
    from .models.imagery.base import KWCOCOArchive
    from .models.imagery.etl import load_kwcoco_dataset

    ds_entry = KWCOCOArchive.objects.get(id=kwcoco_dataset_id)
    try:
        load_kwcoco_dataset(kwcoco_dataset_id)
    except Exception as exc:
        logger.exception(f'Internal error run `load_kwcoco_dataset`: {exc}')
        ds_entry.failure_reason = str(exc)
    ds_entry.save(update_fields=['failure_reason'])
    return
