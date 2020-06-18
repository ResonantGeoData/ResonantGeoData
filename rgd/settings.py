import os
from typing import Type

from configurations import Configuration, values


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# TODO: BASE_DIR is not an actual Django setting, remove it
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# When "environ_name" is specified or "environ=False", a Value will immediately bind (and so
# cannot be tweaked effectively in "before_binding"), unless "late_binding=True"
values.Value.late_binding = True


class ComposedConfiguration(Configuration):
    """
    Abstract base for composed Configuration.

    This must always be specified as a base class after Config mixins.
    """

    @classmethod
    def pre_setup(cls):
        super().pre_setup()

        # For every class in the inheritance hierarchy
        # Reverse order allows more base classes to run first
        for base_cls in reversed(cls.__mro__):
            # If the class has "before_binding" as its own (non-inherited) method
            if 'before_binding' in base_cls.__dict__:
                base_cls.before_binding(cls)

    @classmethod
    def post_setup(cls):
        super().post_setup()

        for base_cls in reversed(cls.__mro__):
            if 'after_binding' in base_cls.__dict__:
                base_cls.after_binding(cls)


class Config:
    """Abstract mixin for composable Config sections."""

    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]) -> None:
        """
        Run before values are fully bound with environment variables.

        `configuration` refers to the final Configuration class, so settings from
        other Configs in the final hierarchy may be referenced.
        """
        pass

    @staticmethod
    def after_binding(configuration: Type[ComposedConfiguration]) -> None:
        """
        Run after values are fully bound with environment variables.

        `configuration` refers to the final Configuration class, so settings from
        other Configs in the final hierarchy may be referenced.
        """
        pass


class DjangoConfig(Config):
    SECRET_KEY = values.SecretValue()
    ALLOWED_HOSTS = values.ListValue(environ_required=True)

    WSGI_APPLICATION = 'rgd.wsgi.application'
    ROOT_URLCONF = 'rgd.urls'

    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.humanize',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.sites',
        'rules.apps.AutodiscoverRulesConfig',  # TODO: need this?
    ]

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'APP_DIRS': True,
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                ],
            },
        },
    ]

    AUTHENTICATION_BACKENDS = [
        'rules.permissions.ObjectPermissionBackend',
        # Needed to login by username in Django admin, regardless of `allauth`
        'django.contrib.auth.backends.ModelBackend',
    ]

    # Password validation
    # https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators
    AUTH_PASSWORD_VALIDATORS = [
        {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
        {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
        {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
        {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
    ]

    # Sites framework
    # django.contrib.sites is required by allauth
    SITE_ID = 1

    # Internationalization
    # https://docs.djangoproject.com/en/3.0/topics/i18n/
    LANGUAGE_CODE = 'en-us'
    USE_TZ = True  # TODO: should either USE_TZ or TIME_ZONE be set?
    TIME_ZONE = 'UTC'
    USE_I18N = True  # TODO: why?
    USE_L10N = True  # TODO: why?


class GeoDjangoConfig(Config):
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


class LoggingConfig(Config):
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            # Based on https://stackoverflow.com/a/20983546
            # TODO: Do we like this format?
            'verbose': {
                'format': (
                    '%(asctime)s [%(process)d] [%(levelname)s] '
                    'pathname=%(pathname)s lineno=%(lineno)s '
                    'funcname=%(funcName)s %(message)s'
                ),
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                # Unlike the Django default "console" handler, this works during production,
                # has a level of DEBUG, and uses a different formatter
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
            'mail_admins': {
                # Disable Django's default "mail_admins" handler
                'class': 'logging.NullHandler',
            },
        },
    }


class StaticFileConfig(Config):
    """
    Static file serving config.

    This could be used directly, but typically is included implicitly by
    WhitenoiseStaticFileConfig.
    """

    STATIC_URL = '/static/'
    STATIC_ROOT = values.PathValue(
        os.path.join(BASE_DIR, 'staticfiles'), environ=False, check_exists=False
    )

    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django.contrib.staticfiles']

    @staticmethod
    def after_binding(configuration: Type[ComposedConfiguration]):
        os.makedirs(configuration.STATIC_ROOT, exist_ok=True)


class WhitenoiseStaticFileConfig(StaticFileConfig):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        # Insert immediately before staticfiles app
        staticfiles_index = configuration.INSTALLED_APPS.index('django.contrib.staticfiles')
        configuration.INSTALLED_APPS.insert(staticfiles_index, 'whitenoise.runserver_nostatic')

        # Insert immediately after SecurityMiddleware
        security_index = configuration.MIDDLEWARE.index(
            'django.middleware.security.SecurityMiddleware'
        )
        configuration.MIDDLEWARE.insert(
            security_index + 1, 'whitenoise.middleware.WhiteNoiseMiddleware'
        )

    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


class AllauthConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        # `allauth` specific authentication methods, such as login by e-mail
        configuration.AUTHENTICATION_BACKENDS += [
            'allauth.account.auth_backends.AuthenticationBackend'
        ]

        configuration.INSTALLED_APPS += [
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
        ]

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


class CorsConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['corsheaders']

        # CorsMiddleware must be added immediately before WhiteNoiseMiddleware, so this can
        # potentially add CORS headers to those responses too.
        # Accordingly, CorsConfig must be loaded after WhitenoiseStaticFileConfig, so it can
        # find the existing entry and insert accordingly.
        try:
            whitenoise_index = configuration.MIDDLEWARE.index(
                'whitenoise.middleware.WhiteNoiseMiddleware'
            )
        except ValueError:
            raise Exception('CorsConfig must be loaded after WhitenoiseStaticFileConfig.')
        configuration.MIDDLEWARE.insert(whitenoise_index, 'corsheaders.middleware.CorsMiddleware')

    CORS_ORIGIN_WHITELIST = values.ListValue()
    CORS_ORIGIN_REGEX_WHITELIST = values.ListValue()


class RestFrameworkConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += [
            'rest_framework',
            'rest_framework.authtoken',
            'drf_yasg',
            'django_filters',
        ]

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication'],
    }


class DatabaseConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['django.contrib.postgres']

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


class CeleryConfig(Config):
    CELERY_BROKER_URL = values.Value('amqp://localhost:5672/')
    CELERY_RESULT_BACKEND = None
    # Only acknowledge a task being done after the function finishes
    CELERY_TASK_ACKS_LATE = True
    # CloudAMQP-suggested settings
    # https://www.cloudamqp.com/docs/celery.html
    CELERY_BROKER_POOL_LIMIT = 1
    CELERY_BROKER_HEARTBEAT = None
    CELERY_BROKER_CONNECTION_TIMEOUT = 30
    CELERY_EVENT_QUEUE_EXPIRES = 60
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    # CELERY_WORKER_CONCURRENCY can be set if workers have resource constraints
    CELERY_WORKER_SEND_TASK_EVENTS = True


class SwaggerConfig(Config):
    REFETCH_SCHEMA_WITH_AUTH = True
    REFETCH_SCHEMA_ON_LOGOUT = True
    OPERATIONS_SORTER = 'alpha'
    DEEP_LINKING = True


class StorageConfig(Config):
    """Abstract base for storage configs."""

    pass
    # For unity, subclasses should use "environ_name='STORAGE_BUCKET_NAME'" for
    # whatever particular setting is used to store the bucket name


class MinioStorageConfig(StorageConfig):
    DEFAULT_FILE_STORAGE = 'minio_storage.storage.MinioMediaStorage'
    MINIO_STORAGE_ENDPOINT = values.Value('localhost:9000')
    MINIO_STORAGE_USE_HTTPS = False
    MINIO_STORAGE_MEDIA_BUCKET_NAME = values.Value(
        environ_name='STORAGE_BUCKET_NAME', environ_required=True
    )
    MINIO_STORAGE_ACCESS_KEY = values.SecretValue()
    MINIO_STORAGE_SECRET_KEY = values.SecretValue()
    MINIO_STORAGE_MEDIA_USE_PRESIGNED = True
    # TODO: Boto config for minio?


class S3StorageConfig(StorageConfig):
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    # This exact environ_name is important, as direct use of Boto will also use it
    AWS_S3_REGION_NAME = values.Value(
        environ_prefix=None, environ_name='AWS_DEFAULT_REGION', environ_required=True
    )  # TODO: this is also used by Boto directly
    AWS_STORAGE_BUCKET_NAME = values.Value(
        environ_name='STORAGE_BUCKET_NAME', environ_required=True
    )
    AWS_S3_MAX_MEMORY_SIZE = 5 * 1024 * 1024
    AWS_S3_FILE_OVERWRITE = False
    AWS_AUTO_CREATE_BUCKET = False
    AWS_QUERYSTRING_EXPIRE = 3600 * 6  # 6 hours
    AWS_DEFAULT_ACL = None


class EmailConfig(Config):
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'ISIC Challenge <support@isic-archive.com>'
    # TODO: Production


class CleanupConfig(Config):
    @staticmethod
    def after_binding(configuration: Type[ComposedConfiguration]):
        # To ensure that exceptions inside other apps' signal handlers do not
        # affect the integrity of file deletions within transactions,
        # this should be placed last in INSTALLED_APPS.
        # So, add it in after_binding, instead of the typical before_binding.
        configuration.INSTALLED_APPS += ['django_cleanup.apps.CleanupConfig']


class CrispyFormsConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['crispy_forms']


class DebugToolbarConfig(Config):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['debug_toolbar']
        configuration.MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
        # TODO: 'django_extensions' ?


class RgdConfig(Config):
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

    # Additional settings for the RGD app can be placed here
    pass


class BaseConfiguration(
    RgdConfig,
    CleanupConfig,
    CrispyFormsConfig,
    EmailConfig,
    CeleryConfig,
    DatabaseConfig,
    RestFrameworkConfig,
    CorsConfig,
    AllauthConfig,
    WhitenoiseStaticFileConfig,
    LoggingConfig,
    DjangoConfig,
    GeoDjangoConfig,
    ComposedConfiguration,
    SwaggerConfig,
):
    # Does not include a StorageConfig, since that varies
    # significantly from development to production
    pass


class DevelopmentConfiguration(DebugToolbarConfig, MinioStorageConfig, BaseConfiguration):
    DEBUG = True
    SECRET_KEY = 'insecuresecret'
    ALLOWED_HOSTS = values.ListValue(['localhost', '127.0.0.1'])
    CORS_ORIGIN_REGEX_WHITELIST = values.ListValue(
        [r'http://localhost:\d+', r'http://127\.0\.0\.1:\d+']
    )

    # INTERNAL_IPS does not work properly when this is run within Docker, since the bridge
    # sends requests from the host machine via a dedicated IP address
    INTERNAL_IPS = ['127.0.0.1']
    # SHOW_TOOLBAR_CALLBACK for debug_toolbar normally relies on INTERNAL_IPS,
    # but force enable it to support Docker mode
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
    }


class ProductionConfiguration(S3StorageConfig, BaseConfiguration):
    pass


class HerokuProductionConfiguration(ProductionConfiguration):
    # Use different env var names (with no DJANGO_ prefix) for services that Heroku auto-injects
    DATABASES = values.DatabaseURLValue(
        environ_name='DATABASE_URL',
        environ_prefix=None,
        environ_required=True,
        engine='django.contrib.gis.db.backends.postgis',
        conn_max_age=600,
        ssl_require=True,
    )
    CELERY_BROKER_URL = values.Value(
        environ_name='CLOUDAMQP_URL', environ_prefix=None, environ_required=True
    )
