from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
import magic

from rgd.utility import _link_url

from ... import tasks
from ..common import ChecksumFile, ModifiableEntry, SpatialEntry
from ..constants import DB_SRID
from ..mixins import Status, TaskEventMixin


def validate_archive(field_file):
    """Validate file is a zip or tar archive."""
    acceptable = ['application/zip', 'application/gzip']

    mimetype = magic.from_buffer(field_file.read(16384), mime=True)

    if mimetype not in acceptable:
        raise ValidationError('Unsupported file archive.')


class GeometryArchive(ModifiableEntry, TaskEventMixin):
    """Container for ``zip`` archives of a shapefile.

    When this model is created, it loads data from an archive into
    a single ``GeometryEntry`` that is then associated with this entry.
    """

    task_func = tasks.task_read_geometry_archive
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE)

    failure_reason = models.TextField(null=True)
    status = models.CharField(max_length=20, default=Status.CREATED, choices=Status.choices)

    def save(self, *args, **kwargs):
        super(GeometryArchive, self).save(*args, **kwargs)

    def archive_data_link(self):
        return _link_url('geodata', 'geometry_archive', self, 'file')

    archive_data_link.allow_tags = True


class GeometryEntry(ModifiableEntry, SpatialEntry):
    """A holder for geometry vector data."""

    name = models.TextField(blank=True)
    description = models.TextField(null=True, blank=True)

    data = models.GeometryCollectionField(srid=DB_SRID)  # Can be one or many features
    # The actual collection is iterable so access is super easy

    # Can be null if not generated from uploaded ZIP file but something else
    geometry_archive = models.OneToOneField(GeometryArchive, null=True, on_delete=models.CASCADE)
