from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.mixins import DetailViewMixin, PermissionPathMixin, TaskEventMixin
from rgd_3d.tasks import jobs


class Tiles3D(TimeStampedModel, TaskEventMixin, PermissionPathMixin, DetailViewMixin):
    class Meta:
        verbose_name = '3D tiles'
        verbose_name_plural = '3D tiles'

    def clean(self):
        if self.json_file.file_set is None:
            raise ValidationError('"json_file" must be part of a FileSet.')
        return super().clean()

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    json_file = models.ForeignKey(
        ChecksumFile,
        on_delete=models.CASCADE,
        related_name='+',
        help_text='The `tileset.json` file that contains metadata about this set of 3D tiles.',
    )

    task_funcs = (jobs.task_read_3d_tiles_file,)
    permissions_paths = [('json_file', ChecksumFile)]
    detail_view_name = 'detail-tiles-3d'


class Tiles3DMeta(TimeStampedModel, SpatialEntry, PermissionPathMixin):
    source = models.OneToOneField(Tiles3D, on_delete=models.CASCADE)

    @property
    def name(self):
        return self.source.json_file.name

    permissions_paths = [('source', Tiles3D)]
    detail_view_name = Tiles3D.detail_view_name
    detail_view_pk = 'source__pk'
