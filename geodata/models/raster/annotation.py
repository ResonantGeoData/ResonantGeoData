from django.contrib.gis.db import models
from django.contrib.postgres import fields
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from s3_file_field import S3FileField

from .base import RasterEntry
from ..common import ModifiableEntry
from ..constants import DB_SRID


class Annotation(ModifiableEntry):
    """Image annotation/label for RasterEntry."""
    raster = models.ForeignKey(RasterEntry, on_delete=models.CASCADE)

    caption = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    bounding_box = models.PolygonField(srid=DB_SRID)
    feature = models.GeometryField(srid=DB_SRID, null=True)
    annotator = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(null=True, blank=True)
