from django.contrib.gis.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..common import ModifiableEntry, PostSaveEventModel, SpatialEntry
from ..constants import DB_SRID


def validate_zip_extension(value):
    import os
    from django.core.exceptions import ValidationError

    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = [
        '.zip',
    ]
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')


class GeometryEntry(SpatialEntry):
    """A holder for geometry vector data."""

    data = models.GeometryCollectionField(srid=DB_SRID)  # Can be one or many features
    # The actual collection is iterable so access is super easy


class GeometryArchive(ModifiableEntry, PostSaveEventModel):
    """Container for ``zip`` archives of a shapefile.

    When this model is created, it loads data from an archive into
    a single ``GeometryEntry`` that is then associated with this entry.
    """

    task_name = 'validate_geometry_archive'
    archive_file = models.FileField(
        upload_to='geometry_files',
        validators=[validate_zip_extension],
        help_text='This must be an archive (`.zip`) of a single shape (`.shp`, `.dbf`, `.shx`, etc.).',
    )

    geometry_entry = models.OneToOneField(GeometryEntry, null=True, on_delete=models.DO_NOTHING)


@receiver(post_save, sender=GeometryArchive)
def _post_save_algorithm(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))
