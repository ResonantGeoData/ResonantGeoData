import os
from pathlib import Path
from typing import Type

from composed_configuration import (
    ComposedConfiguration,
    ConfigMixin,
    DevelopmentBaseConfiguration,
    HerokuProductionBaseConfiguration,
    ProductionBaseConfiguration,
    TestingBaseConfiguration,
)
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


class CrispyFormsMixin(ConfigMixin):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['crispy_forms']


class RgdMixin(CrispyFormsMixin, GeoDjangoMixin, SwaggerMixin, ConfigMixin):
    WSGI_APPLICATION = 'rgd.wsgi.application'
    ROOT_URLCONF = 'rgd.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        # Install local apps first, to ensure any overridden resources are found first
        configuration.INSTALLED_APPS = [
            'rgd.geodata.apps.GeodataConfig',
        ] + configuration.INSTALLED_APPS

        # Install additional apps
        configuration.INSTALLED_APPS += [
            's3_file_field',
            'rules.apps.AutodiscoverRulesConfig',  # TODO: need this?
            # To ensure that exceptions inside other apps' signal handlers do not affect the
            # integrity of file deletions within transactions, CleanupConfig should be last.
            'django_cleanup.apps.CleanupConfig',
        ]

        configuration.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
            'rest_framework.authentication.BasicAuthentication'
        )

        configuration.AUTHENTICATION_BACKENDS.insert(0, 'rules.permissions.ObjectPermissionBackend')

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


class DevelopmentConfiguration(RgdMixin, DevelopmentBaseConfiguration):
    pass


class TestingConfiguration(RgdMixin, TestingBaseConfiguration):
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


class ProductionConfiguration(RgdMixin, ProductionBaseConfiguration):
    pass


class HerokuProductionConfiguration(RgdMixin, HerokuProductionBaseConfiguration):
    # Use different env var names (with no DJANGO_ prefix) for services that Heroku auto-injects
    DATABASES = values.DatabaseURLValue(
        environ_name='DATABASE_URL',
        environ_prefix=None,
        environ_required=True,
        engine='django.contrib.gis.db.backends.postgis',
        conn_max_age=600,
        ssl_require=True,
    )
