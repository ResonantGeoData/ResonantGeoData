from django.apps import AppConfig


class RGDImageryConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'rgd_imagery'

    def ready(self):
        import rgd_imagery.signals  # noqa: F401
