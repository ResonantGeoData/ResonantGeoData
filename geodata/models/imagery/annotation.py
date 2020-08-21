from django.contrib.gis.db import models

from ..common import ModifiableEntry
from ..constants import DB_SRID
from .base import ImageEntry


class Annotation(ModifiableEntry):
    """Image annotation/label for ImageEntry."""

    image = models.ForeignKey(ImageEntry, on_delete=models.CASCADE)

    caption = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    bounding_box = models.PolygonField(srid=DB_SRID)
    feature = models.GeometryField(srid=DB_SRID, null=True)
    annotator = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(null=True, blank=True)
