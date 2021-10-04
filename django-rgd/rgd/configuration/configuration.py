from __future__ import annotations

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
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django.contrib.gis']
        import osgeo

        configuration.GDAL_LIBRARY_PATH = osgeo.GDAL_LIBRARY_PATH
        configuration.GEOS_LIBRARY_PATH = osgeo.GEOS_LIBRARY_PATH


class SwaggerMixin(ConfigMixin):
    REFETCH_SCHEMA_WITH_AUTH = True
    REFETCH_SCHEMA_ON_LOGOUT = True
    OPERATIONS_SORTER = 'alpha'
    DEEP_LINKING = True


class ResonantGeoDataBaseMixin(GeoDjangoMixin, SwaggerMixin, ConfigMixin):
    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:
        configuration.MIDDLEWARE += [
            'crum.CurrentRequestUserMiddleware',
        ]

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
    RGD_STAC_BROWSER_LIMIT = values.Value(default=1000)
