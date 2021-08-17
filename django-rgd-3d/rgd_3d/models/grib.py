from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile
from rgd.models.mixins import PermissionPathMixin, TaskEventMixin
from rgd_3d.tasks import jobs


class GRIB(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """Container for point cloud file."""

    task_funcs = (jobs.task_read_grib_file,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')

    def data_link(self):
        return self.file.data_link()

    data_link.allow_tags = True

    # A place to store converted 3D model - must be in VTI format
    vti_data = models.ForeignKey(
        ChecksumFile, on_delete=models.SET_NULL, blank=True, null=True, related_name='+'
    )

    def _post_delete(self, *args, **kwargs):
        if self.vti_data:
            self.vti_data.delete()

    permissions_paths = [('file', ChecksumFile)]
