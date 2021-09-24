from __future__ import annotations

from pathlib import Path
from typing import Type

from composed_configuration import (
    ComposedConfiguration,
    ConfigMixin,
    DevelopmentBaseConfiguration,
    TestingBaseConfiguration,
)
from composed_configuration_rgd import ResonantGeoDataBaseMixin


class CrispyFormsMixin(ConfigMixin):
    @staticmethod
    def before_binding(configuration: Type[ComposedConfiguration]):
        configuration.INSTALLED_APPS += ['crispy_forms']


class RGDExampleProjectMixin(CrispyFormsMixin, ResonantGeoDataBaseMixin, ConfigMixin):
    WSGI_APPLICATION = 'rgd_example.wsgi.application'
    ROOT_URLCONF = 'rgd_example.urls'

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

    @staticmethod
    def before_binding(configuration: ComposedConfiguration) -> None:

        # Install additional apps
        configuration.INSTALLED_APPS += [  # noqa
            'rgd',
            'rgd_3d',
            'rgd_fmv',
            'rgd_geometry',
            'rgd_imagery',
        ]

        configuration.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'].append(
            'rest_framework.authentication.BasicAuthentication'
        )


class DevelopmentConfiguration(RGDExampleProjectMixin, DevelopmentBaseConfiguration):
    pass


class TestingConfiguration(RGDExampleProjectMixin, TestingBaseConfiguration):
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
