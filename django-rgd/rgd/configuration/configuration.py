from __future__ import annotations

import logging
import os
import tempfile
from typing import Type

try:
    from composed_configuration import ComposedConfiguration, ConfigMixin
    from configurations import values
except ImportError:
    raise ImportError(
        'Please install `django-composed-configuration` and `django-configurations` '
        'to use the configuration mixins. This can be done through the `configuration` '
        'extra when installing `django-rgd`.'
    )


class GeoDjangoMixin(ConfigMixin):
    @staticmethod
    def mutate_configuration(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django.contrib.gis']

        try:
            import osgeo

            configuration.GDAL_LIBRARY_PATH = osgeo.GDAL_LIBRARY_PATH
            configuration.GEOS_LIBRARY_PATH = osgeo.GEOS_LIBRARY_PATH
        except (ImportError, AttributeError):
            logging.warning(
                'GDAL wheel not installed, skipping configuration. If you have not '
                'installed GDAL manually, please install the wheel with the following command: '
                'pip install --find-links https://girder.github.io/large_image_wheels GDAL'
            )


class SwaggerMixin(ConfigMixin):
    REFETCH_SCHEMA_WITH_AUTH = True
    REFETCH_SCHEMA_ON_LOGOUT = True
    OPERATIONS_SORTER = 'alpha'
    DEEP_LINKING = True


class MemachedMixin(ConfigMixin):
    MEMCACHED_URL = values.Value(default=None)
    MEMCACHED_USERNAME = values.Value(default=None)
    MEMCACHED_PASSWORD = values.Value(default=None)
    MEMCACHED_BINARY = values.Value(default=True)
    SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

    @classmethod
    def post_setup(cls):
        super().post_setup()

        if cls.MEMCACHED_URL:
            caches = {
                'default': {
                    'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
                    'LOCATION': cls.MEMCACHED_URL,
                    'OPTIONS': {
                        'binary': cls.MEMCACHED_BINARY,
                    },
                }
            }

            if cls.MEMCACHED_USERNAME and cls.MEMCACHED_PASSWORD:
                caches['default']['OPTIONS']['username'] = cls.MEMCACHED_PASSWORD
                caches['default']['OPTIONS']['password'] = cls.MEMCACHED_USERNAME

            cls.CACHES = caches


class ResonantGeoDataBaseMixin(GeoDjangoMixin, SwaggerMixin, ConfigMixin):
    @staticmethod
    def mutate_configuration(configuration: ComposedConfiguration) -> None:
        configuration.MIDDLEWARE += [
            'crum.CurrentRequestUserMiddleware',
        ]
        configuration.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += [
            'rest_framework.authentication.TokenAuthentication',
        ]

    @classmethod
    def post_setup(cls):
        super().post_setup()
        if getattr(cls, 'DEBUG', False) or cls.RGD_DEBUG_LOGS:
            cls.LOGGING['loggers']['rgd'] = {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': False,
            }

    # This cannot have a default value, since the password and database name are always
    # set by the service admin
    DATABASES = values.DatabaseURLValue(
        environ_name='DATABASE_URL',
        environ_prefix='DJANGO',
        environ_required=True,
        # Additional kwargs to DatabaseURLValue are passed to dj-database-url
        engine='django.contrib.gis.db.backends.postgis',
        conn_max_age=600,
    )

    CELERY_WORKER_SEND_TASK_EVENTS = True

    RGD_FILE_FIELD_PREFIX = values.Value(default=None)
    RGD_GLOBAL_READ_ACCESS = values.Value(default=False)
    RGD_AUTO_APPROVE_SIGN_UP = values.Value(default=False)
    RGD_AUTO_COMPUTE_CHECKSUMS = values.Value(default=False)
    RGD_TEMP_DIR = values.Value(default=os.path.join(tempfile.gettempdir(), 'rgd'))
    RGD_TARGET_AVAILABLE_CACHE = values.Value(default=2)
    RGD_REST_CACHE_TIMEOUT = values.Value(default=60 * 60 * 2)
    RGD_SIGNED_URL_TTL = values.Value(default=60 * 60 * 24)  # 24 hours
    RGD_SIGNED_URL_QUERY_PARAM = values.Value(default='signature')
    RGD_DEBUG_LOGS = values.Value(default=True)
