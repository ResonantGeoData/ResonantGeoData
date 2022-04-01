import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class RGDImageryConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'rgd_imagery'

    def ready(self):
        import rgd_imagery.signals  # noqa: F401
