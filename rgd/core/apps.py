from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'rgd.core'

    def ready(self):
        import rgd.core.signals  # noqa: F401
