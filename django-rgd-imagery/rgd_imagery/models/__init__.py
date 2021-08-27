"""This models contains a model hierarchy for raster datasets.

The ``base`` module contains base classes for representing raster models.
As new data types are introduced to the database, a new model for that data
type should be added, subclassing the appropriate base models.

"""
from .annotation import Annotation, PolygonSegmentation, RLESegmentation, Segmentation

# flake8: noqa
from .base import BandMeta, Image, ImageMeta, ImageSet, ImageSetSpatial
from .kwcoco import KWCOCOArchive
from .processed import ProcessedImage, ProcessedImageGroup
from .raster import Raster, RasterMeta
from .utility import *  # noqa
