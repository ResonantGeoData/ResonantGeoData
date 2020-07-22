import os
from pathlib import Path
from typing import Type

from configurations import values
from django_girders.configuration import (
    ComposedConfiguration,
    ConfigMixin,
    DevelopmentBaseConfiguration,
    HerokuProductionBaseConfiguration,
    ProductionBaseConfiguration,
    TestingBaseConfiguration,
)


class GeoDjangoConfig(ConfigMixin):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django.contrib.gis']

        try:
            import osgeo
            import re

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


class AllauthConfig(ConfigMixin):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        # `allauth` specific authentication methods, such as login by e-mail
        configuration.AUTHENTICATION_BACKENDS += [
            'allauth.account.auth_backends.AuthenticationBackend'
        ]

        configuration.INSTALLED_APPS += [
            'django.contrib.sites',
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
        ]

    # Sites framework
    SITE_ID = 1

    ACCOUNT_AUTHENTICATION_METHOD = 'email'
    ACCOUNT_USERNAME_REQUIRED = False
    ACCOUNT_EMAIL_REQUIRED = True
    ACCOUNT_EMAIL_VERIFICATION = 'optional'

    # This improves lookup performance, but makes the username no longer match the email
    # TODO: Do we want this?
    # TODO: Does it prevent near-duplicate registration?
    ACCOUNT_PRESERVE_USERNAME_CASING = False

    # TODO: Add a migration for contrib.sites, to prevent "example.com" from being used everywhere

    # Always enable "Remember me?", as it is a significant quality of life
    # improvement, and auto-logout for shared devices is a less relevent
    # concern for modern usage scenarios
    ACCOUNT_SESSION_REMEMBER = True

    LOGIN_REDIRECT_URL = '/'
    ACCOUNT_LOGOUT_REDIRECT_URL = '/'

    # Quality of life improvements, but may not work if the browser is closed
    ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
    ACCOUNT_LOGIN_ON_PASSWORD_RESET = True


class SwaggerConfig(ConfigMixin):
    REFETCH_SCHEMA_WITH_AUTH = True
    REFETCH_SCHEMA_ON_LOGOUT = True
    OPERATIONS_SORTER = 'alpha'
    DEEP_LINKING = True


class CrispyFormsConfig(ConfigMixin):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['crispy_forms']


class S3FileFieldConfig(ConfigMixin):
    S3FF_UPLOAD_STS_ARN = ''

    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['s3_file_field']


class RgdConfig(
    S3FileFieldConfig, CrispyFormsConfig, AllauthConfig, GeoDjangoConfig, SwaggerConfig, ConfigMixin
):
    WSGI_APPLICATION = 'rgd.wsgi.application'
    ROOT_URLCONF = 'rgd.urls'

    BASE_DIR = str(Path(__file__).absolute().parent.parent)

    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        # The allauth app also defines a base.html file, so core must be loaded
        # before allauth.
        # Accordingly, RgdConfig must be loaded after AllauthConfig, so it can
        # find the existing entry and insert accordingly.
        try:
            allauth_index = configuration.INSTALLED_APPS.index('allauth')
        except ValueError:
            raise Exception('RgdConfig must be loaded after AllauthConfig.')
        configuration.INSTALLED_APPS.insert(allauth_index, 'geodata')
        configuration.INSTALLED_APPS.insert(allauth_index, 'core')

        configuration.INSTALLED_APPS += [
            'django.contrib.humanize',
            'rules.apps.AutodiscoverRulesConfig',  # TODO: need this?
            # To ensure that exceptions inside other apps' signal handlers do not affect the
            # integrity of file deletions within transactions, CleanupConfig should be last.
            'django_cleanup.apps.CleanupConfig',
        ]

    AUTHENTICATION_BACKENDS = [
        'rules.permissions.ObjectPermissionBackend',
        # Needed to login by username in Django admin, regardless of `allauth`
        'django.contrib.auth.backends.ModelBackend',
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


class DisableS3FileFieldUploadsConfig(ConfigMixin):
    # When minio is in a docker container, there is no sensible route to reach
    # it without setting up a reverse proxy or abusing the hosts file on every
    # client machine.  Rather, disable direct uploads from s3-file-field.  This
    # has to be be done after configuration, as importing s3_file_field has
    # side effects that don't work until other configuration is in place.
    @classmethod
    def post_setup(cls):
        super().post_setup()

        import s3_file_field.configuration

        s3_file_field.configuration.get_storage_provider = (
            lambda: s3_file_field.configuration.StorageProvider.UNSUPPORTED
        )
        s3_file_field.settings._S3FF_STORAGE_PROVIDER = (
            s3_file_field.configuration.StorageProvider.UNSUPPORTED
        )
        s3_file_field.settings._S3FF_ENDPOINT = None


class DevelopmentConfiguration(
    DisableS3FileFieldUploadsConfig, RgdConfig, DevelopmentBaseConfiguration
):
    pass


class TestingConfiguration(RgdConfig, TestingBaseConfiguration):
    MINIO_STORAGE_MEDIA_BUCKET_NAME = 'test-django-storage'


class ProductionConfiguration(RgdConfig, ProductionBaseConfiguration):
    pass


class HerokuProductionConfiguration(RgdConfig, HerokuProductionBaseConfiguration):
    # Use different env var names (with no DJANGO_ prefix) for services that Heroku auto-injects
    DATABASES = values.DatabaseURLValue(
        environ_name='DATABASE_URL',
        environ_prefix=None,
        environ_required=True,
        engine='django.contrib.gis.db.backends.postgis',
        conn_max_age=600,
        ssl_require=True,
    )
