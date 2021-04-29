from django.apps import AppConfig
from django.core.checks import register


class STACConfig(AppConfig):
    name = 'rgd.stac'
    verbose_name = 'SpatioTemporal Asset Catalog'

    def ready(self):
        from rgd.stac.models.extensions import check_model_extensions

        register(check_model_extensions)
