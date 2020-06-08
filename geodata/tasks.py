from celery import shared_task
from celery.utils.log import get_task_logger

# NOTE: do not import `models` to avoid recursive imports

logger = get_task_logger(__name__)


@shared_task(time_limit=86400)
def validate_raster(layer_id):
    from .models.raster.reader import RasterEntryReader

    try:
        reader = RasterEntryReader(layer_id)
        reader.run()
    except Exception as exc:
        logger.exception(f'Internal error run `RasterEntryReader`: {exc}')
        print('!!!!ran into an error!!!!')
    return


@shared_task(time_limit=86400)
def validate_geometry_archive(archive_id):
    from .models.geometry.reader import GeometryArchiveReader

    try:
        print('!!!!running the `GeometryArchiveReader`!!!!')
        reader = GeometryArchiveReader(archive_id)
        reader.run()
    except Exception as exc:
        logger.exception(f'Internal error run `GeometryArchiveReader`: {exc}')
        print('!!!!ran into an error!!!!')
    return
