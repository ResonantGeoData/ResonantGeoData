from django.apps import AppConfig


class RGDConfig(AppConfig):
    name = 'rgd'

    def ready(self):
        import rgd.signals  # noqa: F401
