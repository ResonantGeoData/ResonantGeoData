from rgd import utility

from .. import models
from .base import ImageMetaSerializer, ImageSerializer, ImageSetSerializer
from .processed import ConvertedImageSerializer, RegionImageSerializer
from .raster import RasterMetaSerializer, RasterSerializer
from .stac import STACRasterFeatureSerializer

utility.make_serializers(globals(), models)

__all__ = [
    'ConvertedImageSerializer',
    'ImageSerializer',
    'ImageMetaSerializer',
    'ImageSetSerializer',
    'RasterMetaSerializer',
    'RasterSerializer',
    'RegionImageSerializer',
    'STACRasterFeatureSerializer',
]
