import logging

from rgd.management.commands._data_helper import SynchronousTasksCommand, _get_or_create_file_model
from rgd_fmv import models

logger = logging.getLogger(__name__)

SUCCESS_MSG = 'Finished loading all demo data.'

# Names of files in the datastore
FMV_FILES = []


def load_fmv_files(fmv_files):
    return [_get_or_create_file_model(models.FMV, fmv).id for fmv in fmv_files]


class Command(SynchronousTasksCommand):
    help = 'Populate database with demo data.'

    def handle(self, *args, **options):
        self.set_synchronous()
        # Run the command
        load_fmv_files(FMV_FILES)

        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
        self.reset_celery()
