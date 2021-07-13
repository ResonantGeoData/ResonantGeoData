from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel

from .common import GeospatialFootprint


class BaseAnnotation(TimeStampedModel):
    class Meta:
        abstract = True

    caption = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    annotator = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(null=True, blank=True)
    properties = models.JSONField(null=True, blank=True)


class GeoTemporalAnnotation(BaseAnnotation, GeospatialFootprint):
    """Annotation in world coordinates during a time frame.

    This annotation could be associated with many different spatial entry
    subtypes.

    """

    start_date = models.DateTimeField(null=True, default=None, blank=True)
    end_date = models.DateTimeField(null=True, default=None, blank=True)
