from django.apps import AppConfig


class RGDGeometryConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'rgd_geometry'

    def ready(self):
        import rgd_geometry.signals  # noqa: F401
