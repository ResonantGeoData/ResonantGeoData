from django.apps import AppConfig


class RGDGeometryConfig(AppConfig):
    name = 'rgd_geometry'

    def ready(self):
        import rgd_geometry.signals  # noqa: F401
