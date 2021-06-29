import logging

from rgd.management.commands._data_helper import SynchronousTasksCommand, _get_or_create_file_model
from rgd_geometry import models

logger = logging.getLogger(__name__)


SUCCESS_MSG = 'Finished loading all demo data.'

# Names of files in the datastore
SHAPE_FILES = [
    'Streams.zip',
    'Watershedt.zip',
    'MuniBounds.zip',
    'lm_cnty.zip',
    'dlwatersan.zip',
    'dlschool.zip',
    'dlpark.zip',
    'dlmetro.zip',
    'dllibrary.zip',
    'dlhospital.zip',
    'dlfire.zip',
    'Solid_Mineral_lease_1.zip',
    'AG_lease.zip',
]


def load_shape_files(shape_files):
    ids = []
    for shpfile in shape_files:
        entry = _get_or_create_file_model(models.GeometryArchive, shpfile)
        ids.append(entry.geometrymeta.pk)
    return ids


class Command(SynchronousTasksCommand):
    help = 'Populate database with demo data.'

    def handle(self, *args, **options):
        self.set_synchronous()
        # Run the command
        load_shape_files(SHAPE_FILES)

        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
        self.reset_celery()
