from django.contrib.gis.db import models

from .geometry.base import GeometryEntry
from .raster.base import RasterEntry


class Dataset(models.Model):
    """A general dataset container for spatial entries together.

    Think of this like a collection of data entries for a given project/task.

    Down the road, this model can be subclassed as needed for specific dataset
    types.

    All geospatial info is contained in those data's respective entries.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    geometries = models.ManyToManyField(GeometryEntry)
    rasters = models.ManyToManyField(RasterEntry)
