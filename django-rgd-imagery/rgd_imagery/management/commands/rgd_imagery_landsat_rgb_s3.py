import json

from rgd import datastore
from rgd.management.commands._data_helper import SynchronousTasksCommand

from . import _data_helper as helper

SUCCESS_MSG = 'Finished loading all landsat data.'


def _get_landsat_urls(count):
    path = datastore.datastore.fetch('landsat_texas.json')
    with open(path, 'r') as f:
        scenes = json.loads(f.read())
    if count:
        urls = {}
        for k in list(scenes.keys())[0:count]:
            urls[k] = scenes[k]
    else:
        urls = scenes

    rasters = []
    for name, rf in urls.items():
        rasters.append(
            helper.make_raster_dict(
                [(None, rf['R']), (None, rf['G']), (None, rf['B'])],
                date=rf['acquisition'],
                name=name,
                cloud_cover=rf['cloud_cover'],
                instrumentation='OLI_TIRS',
            )
        )
    return rasters


class Command(SynchronousTasksCommand):
    help = 'Populate database with demo landsat data from S3.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--count', type=int, help='Indicates the number scenes to fetch.', default=0
        )
        parser.add_argument(
            '-g', '--get_count', help='Use to fetch the number of available rasters.'
        )

    def handle(self, *args, **options):
        self.set_synchronous()

        if options.get('get_count', False):
            n = len(_get_landsat_urls(0))
            self.stdout.write(self.style.SUCCESS(f'Total of {n} rasters.'))
            return

        count = options.get('count', 0)

        # Run the command
        helper.load_raster_files(_get_landsat_urls(count))
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
        self.reset_celery()
