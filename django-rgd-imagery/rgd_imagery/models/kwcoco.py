from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile
from rgd.models.mixins import TaskEventMixin
from rgd_imagery.tasks import jobs

from .base import ImageSet


class KWCOCOArchive(TimeStampedModel, TaskEventMixin):
    """A container for holding imported KWCOCO datasets.

    User must upload a JSON file of the KWCOCO meta info and an optional
    archive of images - optional because images can come from URLs instead of
    files.

    """

    task_funcs = (jobs.task_load_kwcoco_dataset,)
    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)
    spec_file = models.OneToOneField(
        ChecksumFile,
        on_delete=models.CASCADE,
        related_name='kwcoco_spec_file',
        help_text='The JSON spec file.',
    )
    image_archive = models.OneToOneField(
        ChecksumFile,
        null=True,
        on_delete=models.CASCADE,
        related_name='kwcoco_image_archive',
        help_text='An archive (.tar or .zip) of the images referenced by the spec file (optional).',
    )
    # Allowed null because model must be saved before task can populate this
    image_set = models.OneToOneField(ImageSet, on_delete=models.SET_NULL, null=True)

    def _post_delete(self, *args, **kwargs):
        # First delete all the images in the image set
        #  this will cascade to the annotations
        images = self.image_set.images.all()
        for image in images:
            # This should cascade to the Image and the ImageMeta
            image.file.delete()
        # Now delete the empty image set
        self.image_set.delete()
