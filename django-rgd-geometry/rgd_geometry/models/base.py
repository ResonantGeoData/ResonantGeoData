from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel
import magic
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.constants import DB_SRID
from rgd.models.mixins import DetailViewMixin, PermissionPathMixin, TaskEventMixin
from rgd_geometry.tasks import jobs


def validate_archive(field_file):
    """Validate file is a zip or tar archive."""
    acceptable = ['application/zip', 'application/gzip']

    mimetype = magic.from_buffer(field_file.read(16384), mime=True)

    if mimetype not in acceptable:
        raise ValidationError('Unsupported file archive.')


class GeometryArchive(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """Container for ``zip`` archives of a shapefile.

    When this model is created, it loads data from an archive into
    a single ``Geometry`` that is then associated with this entry.
    """

    task_funcs = (jobs.task_read_geometry_archive,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')

    def save(self, *args, **kwargs):
        super(GeometryArchive, self).save(*args, **kwargs)

    def archive_data_link(self):
        return self.file.data_link()

    archive_data_link.allow_tags = True

    permissions_paths = [('file', ChecksumFile)]


class Geometry(TimeStampedModel, SpatialEntry, PermissionPathMixin, DetailViewMixin):
    """A holder for geometry vector data."""

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    data = models.GeometryCollectionField(srid=DB_SRID)  # Can be one or many features
    # The actual collection is iterable so access is super easy

    # Can be null if not generated from uploaded ZIP file but something else
    geometry_archive = models.OneToOneField(GeometryArchive, null=True, on_delete=models.CASCADE)

    permissions_paths = [('geometry_archive', GeometryArchive)]
    detail_view_name = 'geometry-entry-detail'
