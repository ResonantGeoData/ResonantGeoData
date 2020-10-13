"""This models contains a model heirarchy for raster datasets.

The ``base`` module contains base classes for representing raster models.
As new data types are introduced to the database, a new model for that data
type should be added, subclassing the appropriate base models.

"""
from .annotation import Annotation, PolygonSegmentation, RLESegmentation, Segmentation

# flake8: noqa
from .base import (
    BandMetaEntry,
    ConvertedImageFile,
    ImageEntry,
    ImageSet,
    KWCOCOArchive,
    RasterEntry,
    Thumbnail,
)
from .ifiles import ImageFile
