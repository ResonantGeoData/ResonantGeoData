import logging

from django.conf import settings
import large_image
from pkg_resources import DistributionNotFound, get_distribution

try:
    __version__ = get_distribution('django-rgd-imagery').version
except DistributionNotFound:
    # package is not installed
    __version__ = None


logger = logging.getLogger(__name__)

# Set config options for large_image
if hasattr(settings, 'RGD_MEMCACHED_URL') and settings.RGD_MEMCACHED_URL:
    large_image.config.setConfig('cache_memcached_url', settings.RGD_MEMCACHED_URL)
    if hasattr(settings, 'RGD_MEMCACHED_USERNAME') and settings.RGD_MEMCACHED_USERNAME:
        large_image.config.setConfig('cache_memcached_username', settings.RGD_MEMCACHED_USERNAME)
        large_image.config.setConfig('cache_memcached_password', settings.RGD_MEMCACHED_PASSWORD)
    large_image.config.setConfig('cache_backend', 'memcached')
    logger.info('Configured for memcached.')
else:
    logger.info('Settings not properly configured for memcached.')
