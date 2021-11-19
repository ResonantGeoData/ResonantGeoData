__all__ = ['download', 'CACHE_TIMEOUT']

from django.conf import settings

from . import download

try:
    CACHE_TIMEOUT = settings.RGD_REST_CACHE_TIMEOUT
except AttributeError:
    CACHE_TIMEOUT = 60 * 60 * 2
