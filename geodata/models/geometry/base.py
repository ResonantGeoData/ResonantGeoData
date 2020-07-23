from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
import magic
from s3_file_field import S3FileField

from ..common import ChecksumFile, SpatialEntry
from ..constants import DB_SRID
from ..mixins import TaskEventMixin
from ... import tasks


def validate_archive(field_file):
    """Validate file is a zip or tar archive."""
    acceptable = ['application/zip', 'application/gzip']

    mimetype = magic.from_buffer(field_file.read(16384), mime=True)

    if mimetype not in acceptable:
        raise ValidationError('Unsupported file archive.')


class GeometryArchive(ChecksumFile, TaskEventMixin):
    """Container for ``zip`` archives of a shapefile.

    When this model is created, it loads data from an archive into
    a single ``GeometryEntry`` that is then associated with this entry.
    """

    task_func = tasks.task_validate_geometry_archive
    file = S3FileField(
        upload_to='files/geometry_files',
        validators=[validate_archive],
        help_text='This must be an archive (`.zip` or `.tar`) of a single shape (`.shp`, `.dbf`, `.shx`, etc.).',
    )

    failure_reason = models.TextField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = self.file.name
        super(GeometryArchive, self).save(*args, **kwargs)


class GeometryEntry(SpatialEntry):
    """A holder for geometry vector data."""

    data = models.GeometryCollectionField(srid=DB_SRID)  # Can be one or many features
    # The actual collection is iterable so access is super easy

    geometry_archive = models.OneToOneField(GeometryArchive, null=True, on_delete=models.CASCADE)


@receiver(post_save, sender=GeometryArchive)
def _post_save_geometry_archive(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))
