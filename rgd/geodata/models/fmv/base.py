import base64
import pickle

from django.contrib.gis.db import models
from s3_file_field import S3FileField

from rgd.utility import _link_url

from ... import tasks
from ..common import ChecksumFile, ModifiableEntry, SpatialEntry
from ..constants import DB_SRID
from ..mixins import TaskEventMixin


class FMVFile(ModifiableEntry, TaskEventMixin):
    """For uploading single FMV files (mp4)."""

    task_funcs = (tasks.task_read_fmv_file,)
    failure_reason = models.TextField(null=True)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE)

    # Allow these to be null because autogenerated
    klv_file = S3FileField(null=True)
    web_video_file = S3FileField(null=True)
    frame_rate = models.FloatField(null=True)

    def fmv_data_link(self):
        return self.file.data_link()

    fmv_data_link.allow_tags = True

    def klv_data_link(self):
        return _link_url(self, 'klv_file')

    klv_data_link.allow_tags = True


class FMVEntry(ModifiableEntry, SpatialEntry):
    """Single FMV entry, tracks the original file."""

    def __str__(self):
        return f'{self.name} ({self.id})'

    name = models.CharField(max_length=1000)
    description = models.TextField(null=True, blank=True)

    fmv_file = models.OneToOneField(FMVFile, on_delete=models.CASCADE)

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
