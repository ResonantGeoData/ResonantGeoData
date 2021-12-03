__all__ = ['CACHE_TIMEOUT']

from django.conf import settings

try:
    CACHE_TIMEOUT = settings.RGD_REST_CACHE_TIMEOUT
except AttributeError:
    CACHE_TIMEOUT = 60 * 60 * 2
