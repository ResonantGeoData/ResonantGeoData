from celery import shared_task
from rgd.tasks import helpers


@shared_task(time_limit=86400)
def task_read_fmv_file(file_pk):
    from rgd_fmv.models import FMV

    from .etl import read_fmv_file

    fmv_file = FMV.objects.get(pk=file_pk)
    helpers._run_with_failure_reason(fmv_file, read_fmv_file, file_pk)
