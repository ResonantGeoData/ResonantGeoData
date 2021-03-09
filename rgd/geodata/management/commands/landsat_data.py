import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError

from . import _data_helper as helper

SUCCESS_MSG = 'Finished loading all landsat data.'


def _get_landsat_urls(count):
    path = os.path.join(os.path.dirname(__file__), 'landsat_texas.json')
    with open(path, 'r') as f:
        scenes = json.loads(f.read())
    if count:
        urls = {}
        for k in list(scenes.keys())[0:count]:
            urls[k] = scenes[k]
    else:
        urls = scenes
    return urls


class Command(BaseCommand):
    help = 'Populate database with demo landsat data from S3.'

    def add_arguments(self, parser):
        parser.add_argument('-c', '--count', type=int, help='Indicates the number scenes to fetch.')
        parser.add_argument(
            '-g', '--get_count', help='Use to fetch the number of available rasters.'
        )

    def handle(self, *args, **options):
        # Set celery to run all tasks synchronously
        eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
        prop = getattr(settings, 'CELERY_TASK_EAGER_PROPAGATES', False)
        # settings.CELERY_TASK_ALWAYS_EAGER = True
        # settings.CELERY_TASK_EAGER_PROPAGATES = True

        if options.get('get_count', False):
            n = len(_get_landsat_urls(0))
            self.stdout.write(self.style.SUCCESS(f'Total of {n} rasters.'))
            return

        count = options.get('count', 0)

        # Run the command
        helper.load_raster_files(_get_landsat_urls(count))
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))

        # Reset celery to previous settings
        settings.CELERY_TASK_ALWAYS_EAGER = eager
        settings.CELERY_TASK_EAGER_PROPAGATES = prop
