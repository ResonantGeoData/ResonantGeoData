from __future__ import annotations

import os
from typing import Type

from composed_configuration import ComposedConfiguration, ConfigMixin
from configurations import values


class GeoDjangoMixin(ConfigMixin):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django.contrib.gis']
        try:
            import re

            import osgeo

            libsdir = os.path.join(
                os.path.dirname(os.path.dirname(osgeo._gdal.__file__)), 'GDAL.libs'
            )
            libs = {
                re.split(r'-|\.', name)[0]: os.path.join(libsdir, name)
                for name in os.listdir(libsdir)
            }
            configuration.GDAL_LIBRARY_PATH = libs['libgdal']
            configuration.GEOS_LIBRARY_PATH = libs['libgeos_c']
        except Exception:
            # TODO: Log that we aren't using the expected GDAL wheel?
            pass


class SwaggerMixin(ConfigMixin):
    REFETCH_SCHEMA_WITH_AUTH = True
    REFETCH_SCHEMA_ON_LOGOUT = True
    OPERATIONS_SORTER = 'alpha'
    DEEP_LINKING = True


class ResonantGeoDataBaseMixin(GeoDjangoMixin, SwaggerMixin, ConfigMixin):
    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:
        configuration.MIDDLEWARE += ('crum.CurrentRequestUserMiddleware',)

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
