from celery import shared_task
from celery.utils.log import get_task_logger

# NOTE: do not import `models` to avoid recursive imports

logger = get_task_logger(__name__)


@shared_task(time_limit=86400)
def validate_raster(file_id):
    from .models.raster.reader import RasterEntryReader, RasterFile

    raster_file = RasterFile.objects.get(id=file_id)
    try:
        reader = RasterEntryReader(file_id)
        reader.run()
        raster_file.failure_reason = ''
    except Exception as exc:
        logger.exception(f'Internal error run `RasterEntryReader`: {exc}')
        raster_file.failure_reason = str(exc)
    raster_file.save(update_fields=['failure_reason'])
    return


@shared_task(time_limit=86400)
def validate_geometry_archive(archive_id):
    from .models.geometry.reader import GeometryArchive, GeometryArchiveReader

    archive = GeometryArchive.objects.get(id=archive_id)
    try:
        reader = GeometryArchiveReader(archive_id)
        reader.run()
        archive.failure_reason = ''
    except Exception as exc:
        logger.exception(f'Internal error run `GeometryArchiveReader`: {exc}')
        archive.failure_reason = str(exc)
    archive.save(update_fields=['failure_reason'])
    return
