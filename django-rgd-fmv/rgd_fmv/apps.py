from django.apps import AppConfig


class RGDFMVConfig(AppConfig):
    name = 'rgd_fmv'

    def ready(self):
        import rgd_fmv.signals  # noqa: F401
