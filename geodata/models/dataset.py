from django.contrib.gis.db import models

from .common import ModifiableEntry


class Dataset(models.Model):
    """A general dataset container for grouping any entries together.

    Think of this like a collection of data entries for a given project/task.

    Down the road, this model can be subclassed as needed for specific
    project needs.

    This can group any ``ModifiableEntry``s together. e.g. files, rasters,
    images, etc.
    """

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    entries = models.ManyToManyField(ModifiableEntry)
