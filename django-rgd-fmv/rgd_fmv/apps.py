from django.apps import AppConfig


class RGDFMVConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'rgd_fmv'

    def ready(self):
        import rgd_fmv.signals  # noqa: F401
