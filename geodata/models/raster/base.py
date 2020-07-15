"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.contrib.postgres import fields
from s3_file_field import S3FileField

from .ifiles import RasterFile
from ..common import ChecksumFile, ModifiableEntry, SpatialEntry
from ..constants import DB_SRID


class RasterEntry(SpatialEntry):
    """This class is a container for the metadata of a raster.

    This model does not hold any raster data, only the metadata, and points
    to a ``RasterFile`` in which keeps track of the actual data.

    """

    instrumentation = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='The instrumentation used to acquire these data.',
    )

    # READ ONLY ATTRIBUTES
    # i.e. these are populated programatically by the ETL routine

    raster_file = models.OneToOneField(RasterFile, null=True, on_delete=models.CASCADE)
    # thumbnail = models.ImageField(blank=True, upload_to='thumbnails')

    # Outline of where there are non-null pixels
    outline = models.PolygonField(srid=DB_SRID, null=True)

    # Raster fields
    crs = models.TextField(help_text='PROJ string')  # PROJ String
    origin = fields.ArrayField(models.FloatField(), size=2)
    extent = fields.ArrayField(models.FloatField(), size=4)
    resolution = fields.ArrayField(models.FloatField(), size=2)  # AKA scale
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    number_of_bands = models.PositiveIntegerField()
    driver = models.CharField(max_length=100)
    metadata = fields.JSONField(null=True)
    # TODO: skew/transform
    transform = fields.ArrayField(models.FloatField(), size=6)


class BandMetaEntry(ModifiableEntry):
    """A basic container to keep track of useful band info."""

    description = models.TextField(
        null=True,
        blank=True,
        help_text='Automatically retreived from raster but can be overwritten.',
    )
    dtype = models.CharField(max_length=10)
    max = models.FloatField(null=True)
    min = models.FloatField(null=True)
    mean = models.FloatField(null=True)
    std = models.FloatField(null=True)
    nodata_value = models.FloatField(null=True)
    parent_raster = models.ForeignKey(RasterEntry, on_delete=models.CASCADE)
    interpretation = models.TextField(null=True, blank=True)


class ConvertedRasterFile(ChecksumFile):
    """A model to store converted versions of a raster entry."""

    file = S3FileField()
    failure_reason = models.TextField(null=True, blank=True)
    source_raster = models.ForeignKey(RasterEntry, on_delete=models.CASCADE)
