from rgd import utility

from . import stac
from .. import models
from .base import ImageMetaSerializer, ImageSerializer, ImageSetSerializer
from .processed import ProcessedImageGroupSerializer, ProcessedImageSerializer
from .raster import RasterMetaSerializer, RasterSerializer

utility.make_serializers(globals(), models)

__all__ = [
    'ImageSerializer',
    'ImageMetaSerializer',
    'ImageSetSerializer',
    'ProcessedImageGroupSerializer',
    'ProcessedImageSerializer',
    'RasterMetaSerializer',
    'RasterSerializer',
    'RegionImageSerializer',
    'stac',
]
