from celery import shared_task

from . import helpers


@shared_task(time_limit=86400)
def task_checksum_file_post_save(checksumfile_id):
    from rgd.models import ChecksumFile

    obj = ChecksumFile.objects.get(id=checksumfile_id)

    helpers._run_with_failure_reason(obj, obj.post_save_job)
