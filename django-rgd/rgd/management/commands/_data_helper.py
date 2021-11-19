import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import URLValidator
from rgd import models
from rgd.datastore import datastore
from rgd.utility import get_or_create_no_commit


class SynchronousTasksCommand(BaseCommand):
    def set_synchronous(self):
        # Set celery to run all tasks synchronously
        self._eager = getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
        self._prop = getattr(settings, 'CELERY_TASK_EAGER_PROPAGATES', False)
        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_EAGER_PROPAGATES = True

    def reset_celery(self):
        # Reset celery to previous settings
        settings.CELERY_TASK_ALWAYS_EAGER = self._eager
        settings.CELERY_TASK_EAGER_PROPAGATES = self._prop


def _save_signal(entry, created):
    if not created and entry.status == models.mixins.Status.SUCCEEDED:
        entry.skip_signal = True
    entry.save()


def _get_or_create_checksum_file_url(url, name=None):
    URLValidator()(url)  # raises `ValidationError` if not a valid URL
    try:
        file_entry = models.ChecksumFile.objects.get(url=url)
        _save_signal(file_entry, False)
        if name:
            file_entry.name = name
            file_entry.save(update_fields=['name'])
    except models.ChecksumFile.DoesNotExist:
        file_entry = models.ChecksumFile()
        file_entry.url = url
        file_entry.type = models.FileSourceType.URL
        if not name:
            # this is to prevent calling `urlopen` in the save to get the file name.
            # this is not a great way to set the default name, but its fast
            name = os.path.basename(url)
        file_entry.name = name
        _save_signal(file_entry, True)
    return file_entry


def _get_or_create_checksum_file_datastore(file, name=None):
    try:
        file_entry = models.ChecksumFile.objects.get(name=file)
        _save_signal(file_entry, False)
    except models.ChecksumFile.DoesNotExist:
        path = datastore.fetch(file)
        file_entry = models.ChecksumFile()
        if name:
            file_entry.name = name
        else:
            file_entry.name = file
        with open(path, 'rb') as f:
            file_entry.file.save(os.path.basename(path), f)
        file_entry.type = models.FileSourceType.FILE_FIELD
        _save_signal(file_entry, True)
    return file_entry


def _get_or_create_checksum_file(file, name=None):
    # Check if there is already an image file with this URL or name
    #  to avoid duplicating data
    try:
        file_entry = _get_or_create_checksum_file_url(file, name=name)
    except ValidationError:
        file_entry = _get_or_create_checksum_file_datastore(file, name=name)
    return file_entry


def _get_or_create_file_model(model, file, name=None):
    # For models that point to a `ChecksumFile`
    file_entry = _get_or_create_checksum_file(file, name=name)
    # No commit in case we need to skip the signal
    entry, created = get_or_create_no_commit(model, file=file_entry)
    _save_signal(entry, created)
    return entry
