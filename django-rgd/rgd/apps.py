from django.apps import AppConfig


class RGDConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'rgd'

    def ready(self):
        import rgd.signals  # noqa: F401
