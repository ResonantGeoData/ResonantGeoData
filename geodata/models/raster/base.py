"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..common import DeferredFieldsManager, ModifiableEntry, PostSaveEventModel, SpatialEntry
from ..constants import DB_SRID
from ... import tasks


class RasterFile(ModifiableEntry, PostSaveEventModel):
    """This is a standalone DB entry for raster files.

    This will automatically generate a ``RasterEntry`` on the post_save event.
    This points to data in its original location.

    TODO: support file collections (e.g. one Landsat 8 entry may need to point
    to a file for each band).

    """

    task_func = tasks.validate_raster
    # TODO: does `raster_file` handle all our use cases?
    raster_file = models.FileField(upload_to='rasters')
    failure_reason = models.TextField(null=True, blank=True)


class RasterEntry(SpatialEntry):
    """This class is a container for the metadata of a raster.

    This model contains a ``GDALRaster`` which does not hold any raster data,
    only the metadata.

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
    raster_file = models.OneToOneField(RasterFile, null=True, on_delete=models.CASCADE)
    raster = models.RasterField(srid=DB_SRID)
    # thumbnail = models.ImageField(blank=True, upload_to='thumbnails')
    # Make sure we do not load the raster each time the model is accessed
    objects = DeferredFieldsManager('raster')  # TODO: does this still need to be deferred?
    footprint = models.PolygonField()

    # Raster fields
    number_of_bands = models.PositiveIntegerField()
    driver = models.CharField(max_length=100, null=True, blank=True,)


class ConvertedRasterFile(ModifiableEntry):
    """A model to store converted versions of a raster entry."""

    converted_file = models.FileField()  # TODO: is this correct?
    failure_reason = models.TextField(null=True, blank=True)
    source_raster = models.ForeignKey(RasterEntry, on_delete=models.CASCADE)


@receiver(post_save, sender=RasterFile)
def _post_save_algorithm(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))
