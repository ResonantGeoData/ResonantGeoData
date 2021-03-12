from django.conf import settings
from django.core.management.base import BaseCommand  # , CommandError

from . import _data_helper as helper

SUCCESS_MSG = 'Finished loading all demo data.'

FMV_FILES = [
    'https://data.kitware.com/api/v1/file/604a547c2fa25629b93176d2/download',
]


class Command(BaseCommand):
    help = 'Populate database with WASABI FMV demo data.'

    def handle(self, *args, **options):
        # Set celery to run all tasks synchronously
        eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
        prop = getattr(settings, 'CELERY_TASK_EAGER_PROPAGATES', False)
        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_EAGER_PROPAGATES = True

        # Run the command
        helper.load_fmv_files(FMV_FILES)
        self.stdout.write(self.style.SUCCESS(SUCCESS_MSG))

        # Reset celery to previous settings
        settings.CELERY_TASK_ALWAYS_EAGER = eager
        settings.CELERY_TASK_EAGER_PROPAGATES = prop
