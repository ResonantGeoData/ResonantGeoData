from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile
from rgd.models.mixins import PermissionPathMixin, TaskEventMixin
from rgd_imagery.tasks import jobs

from .base import Image


class _ProcessedImageBase(TimeStampedModel, TaskEventMixin):
    class Meta:
        abstract = True

    # Processing outputs:
    processed_image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, related_name='+'
    )
    ancillary_files = models.ManyToManyField(ChecksumFile, blank=True, related_name='+')

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated Image and ChecksumFile
        if self.processed_image:
            self.processed_image.file.delete()


class ProcessedImageGroup(TimeStampedModel, PermissionPathMixin):
    source_images = models.ManyToManyField(
        Image,
        through='ProcessedImage',
        through_fields=(
            'group',
            'source_image',
        ),
    )

    permissions_paths = [('source_images', Image)]


class ProcessedImage(_ProcessedImageBase, PermissionPathMixin):
    """Base class for processed images (one-to-one)."""

    task_funcs = (jobs.task_run_processed_image,)

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
    source_image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='+')

    permissions_paths = [('source_image', Image)]


# class CompiledImages(_ProcessedImageBase, PermissionPathMixin):
#     """Base class for compiling images together with a single result (many-to-one)."""
#
#     source_images = models.ManyToManyField(Image, related_name='+')
#
#     permissions_paths = [('source_images', Image)]
