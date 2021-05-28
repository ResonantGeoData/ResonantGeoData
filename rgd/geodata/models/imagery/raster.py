from django.contrib.gis.db import models
from django.contrib.postgres import fields
from django.core.validators import MaxValueValidator, MinValueValidator

from ... import tasks
from ..common import ChecksumFile, ModifiableEntry, SpatialEntry
from ..mixins import TaskEventMixin
from .base import ImageSet


class RasterEntry(ModifiableEntry, TaskEventMixin):
    """This class is a container for the metadata of a raster.

    This model inherits from ``ImageSet`` and only adds an extra layer of
    geospatial context to the ``ImageSet``.

    """

    def __str__(self):
        return 'ID: {} {} (type: {})'.format(self.id, self.name, type(self))

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    image_set = models.OneToOneField(ImageSet, on_delete=models.CASCADE)
    ancillary_files = models.ManyToManyField(ChecksumFile, blank=True)

    task_funcs = (
        tasks.task_populate_raster_entry,
        # tasks.task_populate_raster_footprint,
    )

    @property
    def footprint(self):
        """Pointer to RasterMetaEntry footprint."""
        return self.rastermetaentry.footprint

    @property
    def outline(self):
        """Pointer to RasterMetaEntry outline."""
        return self.rastermetaentry.outline

    @property
    def acquisition_date(self):
        """Pointer to RasterMetaEntry acquisition_date."""
        return self.rastermetaentry.acquisition_date

    @property
    def count(self):
        """Get number of bands across all images in image set."""
        n = 0
        for im in self.image_set.images.all():
            n += im.number_of_bands
        return n


class RasterMetaEntry(ModifiableEntry, SpatialEntry):

    parent_raster = models.OneToOneField(RasterEntry, on_delete=models.CASCADE)

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
