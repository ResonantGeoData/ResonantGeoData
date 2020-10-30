from django.apps import AppConfig


class GeodataConfig(AppConfig):
    name = 'rgd.geodata'

    def ready(self):
        import rgd.geodata.signals  # noqa: F401
