from rgd.management.commands._data_helper import SynchronousTasksCommand

from . import _data_helper as helper

SUCCESS_MSG = 'Finished loading all demo data.'

FMV_FILES = [
    'https://data.kitware.com/api/v1/file/604a5a532fa25629b931c673/download',
    # 'https://data.kitware.com/api/v1/file/604a547c2fa25629b93176d2/download',
]


class Command(SynchronousTasksCommand):
    help = 'Populate database with WASABI FMV demo data.'

    def handle(self, *args, **options):
        self.set_synchronous()
        # Run the command
        helper.load_fmv_files(FMV_FILES)
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))
        self.reset_celery()
