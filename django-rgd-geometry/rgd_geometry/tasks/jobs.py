from celery import shared_task
from django.conf import settings
from rgd.tasks import helpers


@shared_task(time_limit=settings.CELERY_TASK_TIME_LIMIT)
def task_read_geometry_archive(archive_pk):
    from rgd_geometry.models import GeometryArchive

    from .etl import read_geometry_archive

    archive = GeometryArchive.objects.get(pk=archive_pk)
    helpers._run_with_failure_reason(archive, read_geometry_archive, archive_pk)
