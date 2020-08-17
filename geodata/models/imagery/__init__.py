"""This models contains a model heirarchy for raster datasets.

The ``base`` module contains base classes for representing raster models.
As new data types are introduced to the database, a new model for that data
type should be added, subclassing the appropriate base models.

"""
from .base import BandMetaEntry, ConvertedImageFile, ImageEntry, ImageSet, KWCOCOArchive, RasterEntry  # noqa
from .annotation import Annotation, PolygonSegmentation, RLESegmentation, Segmentation  # noqa
from .ifiles import ImageFile  # noqa
