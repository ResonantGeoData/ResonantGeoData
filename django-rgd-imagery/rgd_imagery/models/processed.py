from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile
from rgd.models.mixins import PermissionPathMixin, TaskEventMixin
from rgd_imagery.tasks import jobs

from .base import Image


class ProcessedImageGroup(TimeStampedModel, PermissionPathMixin):
    source_images = models.ManyToManyField(
        Image,
        through='ProcessedImage',
        through_fields=(
            'group',
            'source_image',
        ),
    )
    parameters = models.JSONField()

    permissions_paths = [('source_images', Image)]

    def _post_save(self, *args, **kwargs):
        source_images = self.parameters.get('source_images', [])
        process_type = self.parameters.get('process_type', None)
        parameters = self.parameters.get('parameters', {})
        for pk in source_images:
            image = Image.objects.get(pk=pk)
            processed, created = ProcessedImage.objects.get_or_create(
                source_image=image,
                process_type=process_type,
                parameters=parameters,
                group=self,
            )
            if not created:
                processed.save()

    def _post_delete(self, *args, **kwargs):
        processed = ProcessedImage.objects.filter(group=self)
        processed.delete()


class ProcessedImage(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """Base class for processed images (one-to-one)."""

    task_funcs = (jobs.task_run_processed_image,)

    source_image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='+')

    processed_image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, related_name='+'
    )
    ancillary_files = models.ManyToManyField(ChecksumFile, blank=True, related_name='+')

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated Image and ChecksumFile
        if self.processed_image:
            self.processed_image.file.delete()
        for file in self.ancillary_files.all():
            file.delete()

    class ProcessTypes(models.TextChoices):
        ARBITRARY = 'arbitrary', _('Arbitrarily processed externally')
        COG = 'cog', _('Converted to Cloud Optimized GeoTIFF')
        REGION = 'region', _('Extract subregion')
        RESAMPLE = 'resample', _('Resample by factor')

    process_type = models.CharField(
        max_length=20, default=ProcessTypes.ARBITRARY, choices=ProcessTypes.choices
    )
    parameters = models.JSONField(null=True, blank=True)
    group = models.ForeignKey(ProcessedImageGroup, on_delete=models.CASCADE, null=True, blank=True)

    permissions_paths = [('source_image', Image)]


class CompiledImages(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """Base class for compiling images together with a single result (many-to-one)."""

    task_funcs = (jobs.task_run_compiled_images,)

    source_images = models.ManyToManyField(Image, related_name='+')

    processed_images = models.ManyToManyField(Image, blank=True, related_name='+')
    ancillary_files = models.ManyToManyField(ChecksumFile, blank=True, related_name='+')

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated Image and ChecksumFile
        for image in self.processed_images.all():
            image.file.delete()
        for file in self.ancillary_files.all():
            file.delete()

    class CompileTypes(models.TextChoices):
        ARBITRARY = 'arbitrary', _('Arbitrarily compiled externally')

    process_type = models.CharField(
        max_length=20, default=CompileTypes.ARBITRARY, choices=CompileTypes.choices
    )
    parameters = models.JSONField(null=True, blank=True)

    permissions_paths = [('source_images', Image)]
