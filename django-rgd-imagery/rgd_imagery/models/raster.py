from django.contrib.gis.db import models
from django.contrib.postgres import fields
from django.core.validators import MaxValueValidator, MinValueValidator
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.mixins import DetailViewMixin, TaskEventMixin
from rgd_imagery.tasks import jobs

from .base import ImageSet


class Raster(TimeStampedModel, TaskEventMixin):
    """This class is a container for the metadata of a raster.

    This model inherits from ``ImageSet`` and only adds an extra layer of
    geospatial context to the ``ImageSet``.

    """

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)
    extra_fields = models.JSONField(null=True, blank=True)

    image_set = models.OneToOneField(ImageSet, on_delete=models.CASCADE)
    ancillary_files = models.ManyToManyField(ChecksumFile, blank=True, related_name='+')

    task_funcs = (
        jobs.task_populate_raster,
        # jobs.task_populate_raster_footprint,
    )

    @property
    def count(self):
        """Get number of images."""
        return self.image_set.count

    @property
    def number_of_bands(self):
        """Get number of bands across all images in image set."""
        return self.image_set.number_of_bands


class RasterMeta(TimeStampedModel, SpatialEntry, DetailViewMixin):
    detail_view_name = 'raster-entry-detail'

    parent_raster = models.OneToOneField(Raster, on_delete=models.CASCADE)

    # Raster fields
    crs = models.TextField(help_text='PROJ string')  # PROJ String
    origin = fields.ArrayField(models.FloatField(), size=2)
    extent = fields.ArrayField(models.FloatField(), size=4)
    resolution = fields.ArrayField(models.FloatField(), size=2)  # AKA scale
    # TODO: skew/transform
    transform = fields.ArrayField(models.FloatField(), size=6)
    cloud_cover = models.FloatField(
        null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], blank=True
    )

    @property
    def name(self):
        return self.parent_raster.name
