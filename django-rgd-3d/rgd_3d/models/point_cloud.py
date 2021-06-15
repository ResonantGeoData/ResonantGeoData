from django.contrib.gis.db import models
from django.contrib.postgres import fields
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.mixins import PermissionPathMixin, TaskEventMixin
from rgd_3d.tasks import jobs


class PointCloudFile(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """Container for point cloud file."""

    task_funcs = (jobs.task_read_point_cloud_file,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE)

    def data_link(self):
        return self.file.data_link()

    data_link.allow_tags = True

    permissions_paths = ['file__collection__collection_permissions']


class PointCloudEntry(TimeStampedModel, PermissionPathMixin):
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

    permissions_paths = [
        'source__file__collection__collection_permissions',
        'vtp_data__collection__collection_permissions',
    ]


class PointCloudMetaEntry(TimeStampedModel, SpatialEntry, PermissionPathMixin):
    """Optionally register a PointCloudEntry as a SpatialEntry."""

    parent_point_cloud = models.OneToOneField(PointCloudEntry, on_delete=models.CASCADE)

    crs = models.TextField(help_text='PROJ string', blank=True, null=True)  # PROJ String
    # Origin point to map the 0,0,0 point of the point cloud
    origin = fields.ArrayField(models.FloatField(), size=3, blank=True, null=True)

    @property
    def name(self):
        return self.parent_point_cloud.name

    permissions_paths = [
        'parent_point_cloud__source__file__collection__collection_permissions',
        'parent_point_cloud__vtp_data__collection__collection_permissions',
    ]
