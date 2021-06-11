from django.contrib.gis.db import models
from django.contrib.postgres import fields

from ... import tasks
from ..common import ChecksumFile, ModifiableEntry, SpatialEntry
from ..mixins import TaskEventMixin


class PointCloudFile(ModifiableEntry, TaskEventMixin):
    """Container for point cloud file."""

    task_funcs = (tasks.task_read_point_cloud_file,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE)

    def data_link(self):
        return self.file.data_link()

    data_link.allow_tags = True


class PointCloudEntry(ModifiableEntry):
    """Container for converted point cloud data.

    The data here must be stored in VTP format. This can be manually uploaded
    or created automatically via a PointCloudFile upload.
    """

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    # Can be null if not generated from uploaded file
    source = models.OneToOneField(PointCloudFile, null=True, blank=True, on_delete=models.CASCADE)

    # A place to store converted file - must be in VTP format
    vtp_data = models.ForeignKey(ChecksumFile, on_delete=models.DO_NOTHING)

    def data_link(self):
        return self.vtp_data.data_link()

    data_link.allow_tags = True


class PointCloudMetaEntry(ModifiableEntry, SpatialEntry):
    """Optionally register a PointCloudEntry as a SpatialEntry."""

    parent_point_cloud = models.OneToOneField(PointCloudEntry, on_delete=models.CASCADE)

    crs = models.TextField(help_text='PROJ string', blank=True, null=True)  # PROJ String
    # Origin point to map the 0,0,0 point of the point cloud
    origin = fields.ArrayField(models.FloatField(), size=3, blank=True, null=True)

    @property
    def name(self):
        return self.parent_point_cloud.name
