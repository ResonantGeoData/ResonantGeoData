"""Models for handing input files."""
from django.contrib.gis.db import models
from s3_file_field import S3FileField

from rgd.utility import _link_url

from ... import tasks
from ..common import ArbitraryFile, ChecksumFile
from ..mixins import TaskEventMixin


class BaseImageFile(models.Model):
    """Base model/methods for defining an image file."""

    image_file_id = models.AutoField(primary_key=True)

    def get_image(self):
        """Get the image from wherever is located as a file or something.

        This is intended to be used by endpoints that have yet to come.

        """
        raise NotImplementedError()


class ImageFile(ChecksumFile, TaskEventMixin, BaseImageFile):
    """This is a standalone DB entry for image files.

    This points to a single image file in an S3 file field.

    This will automatically generate an ``ImageEntry`` on the ``post_save``
    event. This points to data in its original location and the generated
    ``ImageEntry`` points to this.

    """

    task_func = tasks.task_read_image_file
    failure_reason = models.TextField(null=True, blank=True)
    file = S3FileField()

    def image_data_link(self):
        return _link_url('geodata', 'image_file', self, 'file')

    image_data_link.allow_tags = True


class ImageArchiveFile(BaseImageFile):
    """For images that exist inside of an archive.

    This is used for KWCOCO datasets where a single image exists somewhere
    inside a larger archive that was uploaded. This tracks the parent arhive
    and the relative path to the image file.
    """

    archive = models.ForeignKey(ArbitraryFile, on_delete=models.CASCADE)
    path = models.TextField(help_text='The relative path to the image inside the archive.')
