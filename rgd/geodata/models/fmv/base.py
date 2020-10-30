import base64
import pickle

from django.contrib.gis.db import models
from s3_file_field import S3FileField

from rgd.utility import _link_url

from ... import tasks
from ..common import ChecksumFile, ModifiableEntry, SpatialEntry
from ..constants import DB_SRID
from ..mixins import Status, TaskEventMixin


class FMVFile(ChecksumFile, TaskEventMixin):
    """For uploading single FMV files (mp4)."""

    task_func = tasks.task_read_fmv_file
    failure_reason = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default=Status.CREATED, choices=Status.choices)
    file = S3FileField()

    def fmv_data_link(self):
        return _link_url('geodata', 'fmv_file', self, 'file')

    fmv_data_link.allow_tags = True


class FMVEntry(ModifiableEntry, SpatialEntry):
    """Single FMV entry, tracks the original file."""

    def __str__(self):
        return f'{self.name} ({self.id})'

    name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(null=True, blank=True)

    fmv_file = models.OneToOneField(FMVFile, null=True, on_delete=models.CASCADE)
    klv_file = S3FileField(null=True, blank=True)
    web_video_file = S3FileField(null=True, blank=True)
    frame_rate = models.FloatField(null=True, blank=True)

    ground_frames = models.MultiPolygonField(srid=DB_SRID, null=True, blank=True)
    ground_union = models.MultiPolygonField(srid=DB_SRID, null=True, blank=True)
    flight_path = models.MultiPointField(srid=DB_SRID, null=True, blank=True)
    frame_numbers = models.BinaryField(null=True, blank=True)

    @staticmethod
    def _array_to_blob(array):
        return base64.b64encode(pickle.dumps(array))

    @staticmethod
    def _blob_to_array(blob):
        return pickle.loads(base64.b64decode(blob))

    def klv_data_link(self):
        return _link_url('geodata', 'fmv_entry', self, 'klv_file')

    klv_data_link.allow_tags = True
