from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_read_geometry_archive(archive_pk):
    from rgd_geometry.models import GeometryArchive

    from .etl import read_geometry_archive

    archive = GeometryArchive.objects.get(pk=archive_pk)
    helpers._run_with_failure_reason(archive, read_geometry_archive, archive_pk)
