from django.apps import AppConfig


class RGD3DConfig(AppConfig):
    name = 'rgd_3d'

    def ready(self):
        import rgd_3d.signals  # noqa: F401
