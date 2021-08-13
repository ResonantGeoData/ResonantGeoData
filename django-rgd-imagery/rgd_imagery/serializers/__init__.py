from rgd import utility

from .. import models
from .base import ImageMetaSerializer, ImageSerializer, ImageSetSerializer
from .processed import ProcessedImageGroupSerializer, ProcessedImageSerializer
from .raster import RasterMetaSerializer, RasterSerializer
from .stac import STACRasterSerializer

utility.make_serializers(globals(), models)

__all__ = [
    'ImageSerializer',
    'ImageMetaSerializer',
    'ImageSetSerializer',
    'ProcessedImageGroupSerializer',
    'ProcessedImageSerializer',
    'RasterMetaSerializer',
    'RasterSerializer',
    'STACRasterSerializer',
]
