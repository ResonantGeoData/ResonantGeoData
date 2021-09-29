from celery import shared_task
from django.conf import settings

from . import helpers


@shared_task(time_limit=86400)
def task_checksum_file_post_save(checksumfile_pk):
    from rgd.models import ChecksumFile
    from rgd.models.mixins import Status

    obj = ChecksumFile.objects.get(pk=checksumfile_pk)

    if obj.validate_checksum or getattr(settings, 'RGD_AUTO_COMPUTE_CHECKSUMS', False):
        helpers._run_with_failure_reason(obj, obj.post_save_job)
    else:
        obj.status = Status.SKIPPED
        obj.save(update_fields=['status'])
