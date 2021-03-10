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
    urls = [list(scene.values()) for scene in scenes.values()]
    if count:
        urls = urls[0:count]
    return urls


class Command(BaseCommand):
    help = 'Populate database with demo landsat data from S3.'

    def add_arguments(self, parser):
        parser.add_argument('-c', '--count', type=int, help='Indicates the number scenes to fetch.')

    def handle(self, *args, **options):
        # Set celery to run all tasks synchronously
        eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
        prop = getattr(settings, 'CELERY_TASK_EAGER_PROPAGATES', False)
        # settings.CELERY_TASK_ALWAYS_EAGER = True
        # settings.CELERY_TASK_EAGER_PROPAGATES = True

        count = options.get('count', 0)

        # Run the command
        helper.load_raster_files(_get_landsat_urls(count))
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))

        # Reset celery to previous settings
        settings.CELERY_TASK_ALWAYS_EAGER = eager
        settings.CELERY_TASK_EAGER_PROPAGATES = prop
