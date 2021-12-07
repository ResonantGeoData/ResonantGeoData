from django.contrib.gis.db import models
from django.contrib.postgres import fields
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.mixins import DetailViewMixin, TaskEventMixin
from rgd_3d.tasks import jobs


class Mesh3D(TimeStampedModel, TaskEventMixin, DetailViewMixin):
    """Container for point cloud file."""

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    # Source data uploaded by user in just about any format
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')

    # A place to store converted file - must be in VTP format
    vtp_data = models.ForeignKey(
        ChecksumFile, on_delete=models.DO_NOTHING, related_name='+', null=True, blank=True
    )

    def data_link(self):
        return self.file.data_link()

    def data_link_vtp(self):
        return self.vtp_data.data_link()

    data_link.allow_tags = True
    data_link_vtp.allow_tags = True

    task_funcs = (jobs.task_read_mesh_3d_file,)
    detail_view_name = 'mesh-3d-detail'


class Mesh3DSpatial(TimeStampedModel, SpatialEntry):
    """Optionally register a Mesh3D as a SpatialEntry."""

    source = models.OneToOneField(Mesh3D, on_delete=models.CASCADE)

    crs = models.TextField(help_text='PROJ string', blank=True, null=True)  # PROJ String
    # Origin point to map the 0,0,0 point of the point cloud
    origin = fields.ArrayField(models.FloatField(), size=3, blank=True, null=True)

    @property
    def name(self):
        return self.source.file.name

    detail_view_name = 'mesh-3d-detail'
    detail_view_pk = 'source__pk'
