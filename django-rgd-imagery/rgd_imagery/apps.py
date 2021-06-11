from django.apps import AppConfig


class RGDImageryConfig(AppConfig):
    name = 'rgd_imagery'

    def ready(self):
        import rgd_imagery.signals  # noqa: F401
