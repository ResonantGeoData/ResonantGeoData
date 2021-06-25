import base64
import pickle

from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.constants import DB_SRID
from rgd.models.mixins import DetailViewMixin, PermissionPathMixin, TaskEventMixin
from rgd.utility import _link_url, uuid_prefix_filename
from rgd_fmv.tasks import jobs
from s3_file_field import S3FileField


class FMV(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """For uploading single FMV files (mp4)."""

    task_funcs = (jobs.task_read_fmv_file,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')

    # Allow these to be null because autogenerated
    klv_file = S3FileField(null=True, upload_to=uuid_prefix_filename)
    web_video_file = S3FileField(null=True, upload_to=uuid_prefix_filename)
    frame_rate = models.FloatField(null=True)

    def fmv_data_link(self):
        return self.file.data_link()

    fmv_data_link.allow_tags = True

    def klv_data_link(self):
        return _link_url(self, 'klv_file')

    klv_data_link.allow_tags = True

    permissions_paths = ['file__collection__collection_permissions']


class FMVMeta(TimeStampedModel, SpatialEntry, PermissionPathMixin, DetailViewMixin):
    """Single FMV entry, tracks the original file."""

    fmv_file = models.OneToOneField(FMV, on_delete=models.CASCADE)

    ground_frames = models.MultiPolygonField(srid=DB_SRID)
    ground_union = models.MultiPolygonField(srid=DB_SRID)
    flight_path = models.MultiPointField(srid=DB_SRID)
    frame_numbers = models.BinaryField()

    @staticmethod
    def _array_to_blob(array):
        return base64.b64encode(pickle.dumps(array))

    @staticmethod
    def _blob_to_array(blob):
        return pickle.loads(base64.b64decode(blob))

    permissions_paths = ['fmv_file__file__collection__collection_permissions']
    detail_view_name = 'fmv-entry-detail'

    @property
    def name(self):
        return self.fmv_file.file.name
