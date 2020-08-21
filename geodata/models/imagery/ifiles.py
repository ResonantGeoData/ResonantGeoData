"""Models for handing input files."""
from django.contrib.gis.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from s3_file_field import S3FileField

from ... import tasks
from ..common import ChecksumFile
from ..mixins import TaskEventMixin


class ImageFile(ChecksumFile, TaskEventMixin):
    """This is a standalone DB entry for raster files.

    This will automatically generate a ``RasterEntry`` on the ``post_save``
    event. This points to data in its original location and the generated
    ``RasterEntry`` points to this.

    """

    task_func = tasks.task_read_image_file
    failure_reason = models.TextField(null=True, blank=True)
    file = S3FileField(upload_to='files/rasters')


@receiver(post_save, sender=ImageFile)
def _post_save_image_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))
