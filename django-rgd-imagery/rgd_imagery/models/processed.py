from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile
from rgd.models.mixins import Status, TaskEventMixin
from rgd_imagery.tasks import jobs

from .base import Image


class ProcessedImageGroup(TimeStampedModel):
    class ProcessTypes(models.TextChoices):
        ARBITRARY = 'arbitrary', _('Arbitrarily processed externally')
        COG = 'cog', _('Converted to Cloud Optimized GeoTIFF')
        REGION = 'region', _('Extract subregion')
        RESAMPLE = 'resample', _('Resample by factor')
        MOSAIC = 'mosaic', _('Mosaic multiple images')

    process_type = models.CharField(
        max_length=20, default=ProcessTypes.ARBITRARY, choices=ProcessTypes.choices
    )
    parameters = models.JSONField(null=True, blank=True)

    def _post_save(self, *args, **kwargs):
        source_images = ProcessedImage.objects.filter(group=self)
        for processed_image in source_images:
            if processed_image.status not in [Status.QUEUED, Status.RUNNING]:
                processed_image.save()


class ProcessedImage(TimeStampedModel, TaskEventMixin):
    """Base class for processed images."""

    task_funcs = (jobs.task_run_processed_image,)

    source_images = models.ManyToManyField(Image)

    processed_image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    ancillary_files = models.ManyToManyField(ChecksumFile, blank=True, related_name='+')

    def _pre_delete(self, *args, **kwargs):
        if self.processed_image:
            self.processed_image.file.delete()
        # TODO: clean up ancillary_files - this throws an error when done through the admin interface
        # self.ancillary_files.all().delete()

    group = models.ForeignKey(ProcessedImageGroup, on_delete=models.CASCADE)
