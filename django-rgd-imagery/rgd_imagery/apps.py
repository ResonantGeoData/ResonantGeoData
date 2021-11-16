import logging

from django.apps import AppConfig
from django.conf import settings
import large_image

logger = logging.getLogger(__name__)


class RGDImageryConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'rgd_imagery'

    def ready(self):
        import rgd_imagery.signals  # noqa: F401

        # Set up memcached with large_image
        if hasattr(settings, 'MEMCACHED_URL') and settings.MEMCACHED_URL:
            large_image.config.setConfig('cache_memcached_url', settings.MEMCACHED_URL)
            if (
                hasattr(settings, 'MEMCACHED_USERNAME')
                and settings.MEMCACHED_USERNAME
                and hasattr(settings, 'MEMCACHED_PASSWORD')
                and settings.MEMCACHED_PASSWORD
            ):
                large_image.config.setConfig(
                    'cache_memcached_username', settings.MEMCACHED_USERNAME
                )
                large_image.config.setConfig(
                    'cache_memcached_password', settings.MEMCACHED_PASSWORD
                )
            large_image.config.setConfig('cache_backend', 'memcached')
            logger.info('large_image is configured for memcached.')
