import json

from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from model_utils.managers import InheritanceManager

from .constants import DB_SRID
from .file import ChecksumFile


class SpatialEntry(models.Model):
    """Common model to all geospatial data entries.

    This is intended to be used in a mixin manner.

    """

    # `InheritanceManager` allows us to select inhereted tables via `objects.select_subclasses()`
    objects = InheritanceManager()

    spatial_id = models.AutoField(primary_key=True)

    # Datetime of creation for the dataset
    acquisition_date = models.DateTimeField(null=True, default=None, blank=True)

    # This can be used with GeoDjango's geographic database functions for spatial indexing
    footprint = models.GeometryField(srid=DB_SRID)
    outline = models.GeometryField(srid=DB_SRID)

    instrumentation = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='The instrumentation used to acquire these data.',
    )

    def __str__(self):
        try:
            return 'Spatial ID: {} (ID: {}, type: {})'.format(self.spatial_id, self.id, type(self))
        except AttributeError:
            return super().__str__()

    @property
    def bounds(self):
        extent = {
            'xmin': self.outline.extent[0],
            'ymin': self.outline.extent[1],
            'xmax': self.outline.extent[2],
            'ymax': self.outline.extent[3],
        }
        return extent

    @property
    def bounds_json(self):
        return json.dumps(self.bounds)


class WhitelistedEmail(models.Model):
    """Pre-approve users for sign up by their email."""

    email = models.EmailField()


class SpatialAsset(SpatialEntry, TimeStampedModel):
    """Any spatially referenced file set.

    This can be any collection of files that have a spatial reference and are
    not explicitly handled by the other SpatialEntry subtypes. For example, this
    model can be used to hold a collection of PDF documents or slide decks that
    have a georeference.

    """

    files = models.ManyToManyField(ChecksumFile, related_name='+')
