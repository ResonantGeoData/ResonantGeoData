from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
import magic
from s3_file_field import S3FileField

from ..common import ModifiableEntry, SpatialEntry
from ..constants import DB_SRID
from ..mixins import PostSaveEventMixin
from ... import tasks


def validate_archive(field_file):
    """Validate file is a zip or tar archive."""
    acceptable = ['application/zip', 'application/gzip']

    mimetype = magic.from_buffer(field_file.read(16384), mime=True)

    if mimetype not in acceptable:
        raise ValidationError('Unsupported file archive.')


class GeometryEntry(SpatialEntry):
    """A holder for geometry vector data."""

    data = models.GeometryCollectionField(srid=DB_SRID)  # Can be one or many features
    # The actual collection is iterable so access is super easy


class GeometryArchive(ModifiableEntry, PostSaveEventMixin):
    """Container for ``zip`` archives of a shapefile.

    When this model is created, it loads data from an archive into
    a single ``GeometryEntry`` that is then associated with this entry.
    """

    task_func = tasks.validate_geometry_archive
    archive_file = S3FileField(
        upload_to='files/geometry_files',
        validators=[validate_archive],
        help_text='This must be an archive (`.zip` or `.tar`) of a single shape (`.shp`, `.dbf`, `.shx`, etc.).',
    )

    geometry_entry = models.OneToOneField(GeometryEntry, null=True, on_delete=models.DO_NOTHING)
    failure_reason = models.TextField(null=True, blank=True)


@receiver(post_save, sender=GeometryArchive)
def _post_save_algorithm(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))
