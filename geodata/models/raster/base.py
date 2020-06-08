"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.contrib.postgres import fields
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..common import DeferredFieldsManager, ModifiableEntry, PostSaveEventModel, SpatialEntry
from ..constants import DB_SRID
from ... import tasks


class RasterEntry(SpatialEntry):
    """This class is a container or the actual raster data/image.

    This model contains a ``GDALRaster`` which can contain ``GDALBand``s.

    In many cases, raster data sets will break up their bands into individual
    rasters (like Landsat 8) and so each one of those files would correspond
    to an instance of this model. In other cases, rasters will keep bands in
    a single raster data file with many components. To easily support both
    scenarios, this model allows the raster dataset to have M many components.

    The ``raster`` property/field is read only to the user and a custom task
    loads the given ``raster_file`` to create the ``raster``.

    """

    instrumentation = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='The instrumentation used to acquire these data.',
    )

    # READ ONLY ATTRIBUTES
    # i.e. these are populated programatically
    raster = models.RasterField(srid=DB_SRID)

    n_bands = models.PositiveIntegerField()

    resolution = fields.ArrayField(models.FloatField())

    # thumbnail = models.ImageField(blank=True, upload_to='thumbnails')

    # Make sure we do not load the raster each time the model is accessed
    objects = DeferredFieldsManager('raster')


class RasterFile(ModifiableEntry, PostSaveEventModel):
    """This is a standalone DB entry for raster files.

    This which will automatically generate a ``RasterEntry``.

    """

    task_func = tasks.validate_raster
    raster_file = models.FileField(upload_to='rasters')
    raster_entry = models.OneToOneField(RasterEntry, null=True, on_delete=models.DO_NOTHING)
    failure_reason = models.TextField(null=True, blank=True)


@receiver(post_save, sender=RasterFile)
def _post_save_algorithm(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))
