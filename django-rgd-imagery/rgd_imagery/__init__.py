from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution('django-rgd-imagery').version
except DistributionNotFound:
    # package is not installed
    __version__ = None


from osgeo import gdal
from rgd.utility import get_temp_dir

gdal.SetConfigOption('GDAL_ENABLE_WMS_CACHE', 'YES')
gdal.SetConfigOption('GDAL_DEFAULT_WMS_CACHE_PATH', str(get_temp_dir() / 'gdalwmscache'))
