"""Models for handing input files."""
from django.contrib.gis.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from s3_file_field import S3FileField

from rgd.utility import _field_file_to_local_path, compute_checksum
from ..common import ModifiableEntry
from ..mixins import PostSaveEventMixin
from ... import tasks


class RasterFile(ModifiableEntry, PostSaveEventMixin):
    """This is a standalone DB entry for raster files.

    This will automatically generate a ``RasterEntry`` on the ``post_save``
    event. This points to data in its original location and the generated
    ``RasterEntry`` points to this.

    TODO: support file collections (e.g. one Landsat 8 entry may need to point
    to a file for each band).

    """

    task_func = tasks.validate_raster
    name = models.CharField(max_length=100, blank=True, null=True)
    # TODO: does `raster_file` handle all our use cases?
    raster_file = S3FileField(upload_to='files/rasters')
    failure_reason = models.TextField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True, null=True)
    compute_checksum = models.BooleanField(default=False)  # a flag to recomput the checksum on save

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.raster_file.name
        if self.compute_checksum:
            with _field_file_to_local_path(self.raster_file) as file_path:
                self.checksum = compute_checksum(file_path)
            self.compute_checksum = False
        super(RasterFile, self).save(*args, **kwargs)


@receiver(post_save, sender=RasterFile)
def _post_save_algorithm(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))
