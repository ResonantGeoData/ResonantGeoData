"""Meta classes that list out useful info stored by GeoDjango to make those
data more accessible.
"""
from django.contrib.gis.gdal.raster.source import GDALBand, GDALRaster

class RasterMeta:
    """A meta class to point to ``GDALRaster`` properties.

    ``django.contrib.gis.gdal.raster.source.GDALRaster``
    """
    def __init__(self, raster):
        if not isinstance(raster, GDALRaster):
            raise TypeError("`RasterMeta` only supports `GDALRaster`. `{}` not supported.".format(type(raster)))
        self._raster = raster

    @property
    def height(self):
        return self._raster.height

    @property
    def width(self):
        return self._raster.width

    @property
    def driver(self):
        return self._raster.driver

    @property
    def metadata(self):
        return self._raster.metadata

    @property
    def origin(self):
        return self._raster.origin

    @property
    def scale(self):
        return self._raster.scale

    @property
    def srid(self):
        return self._raster.srid

    @property
    def skew(self):
        return self._raster.skew

    @property
    def extent(self):
        return self._raster.extent

    @property
    def info(self):
        return self._raster.info



class BandMeta:
    """A meta class to point to ``GDALBand`` properties.

    ``django.contrib.gis.gdal.raster.band.GDALBand``
    """
    def __init__(self, band):
        if not isinstance(raster, GDALBand):
            raise TypeError("`BandMeta` only supports `GDALBand`. `{}` not supported.".format(type(raster)))
        self._band = band

    @property
    def height(self):
        return self._band.height

    @property
    def width(self):
        return self._band.width

    @property
    def description(self):
        return self._band.description

    @property
    def max(self):
        return self._band.max

    @property
    def mean(self):
        return self._band.mean

    @property
    def min(self):
        return self._band.min

    @property
    def metadata(self):
        return self._band.metadata

    @property
    def nodata_value(self):
        return self._band.nodata_value

    @property
    def pixel_count(self):
        return self._band.pixel_count

    @property
    def std(self):
        return self._band.std
