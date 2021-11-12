from pkg_resources import DistributionNotFound, get_distribution
import logging

from django.conf import settings
import large_image

try:
    __version__ = get_distribution('django-rgd-imagery').version
except DistributionNotFound:
    # package is not installed
    __version__ = None


logger = logging.getLogger(__name__)

# Set config options for large_image
try:
    large_image.config.setConfig('cache_memcached_url', getattr(settings, 'RGD_MEMCACHED_URL'))
    if hasattr(settings, 'RGD_MEMCACHED_USERNAME'):
        large_image.config.setConfig(
            'cache_memcached_username', getattr(settings, 'RGD_MEMCACHED_USERNAME')
        )
        large_image.config.setConfig(
            'cache_memcached_password', getattr(settings, 'RGD_MEMCACHED_PASSWORD')
        )
    large_image.config.setConfig('cache_backend', 'memcached')
    logger.info('Configured for memcached.')
except AttributeError:
    logger.info('Settings not properly configured for memcached.')
