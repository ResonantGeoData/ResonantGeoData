from datetime import datetime
from functools import reduce
import logging
import os

import dateutil.parser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.core.validators import URLValidator
from django.db.models import Count
from django.utils.timezone import make_aware

from rgd.geodata import models
from rgd.geodata.datastore import datastore
from rgd.utility import get_or_create_no_commit

logger = logging.getLogger(__name__)


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


def make_raster_dict(
    images,
    name=None,
    date=None,
    cloud_cover=None,
    ancillary_files=None,
    instrumentation=None,
):
    if not isinstance(images[0], tuple):
        images = [(None, im) for im in images]
    return {
        # images is expect to be a list of tuples
        'images': images,
        'name': name,
        'acquisition_date': date,
        'cloud_cover': cloud_cover,
        # ancillary is expected to be list of tuples for URL files ONLY
        'ancillary_files': ancillary_files,
        'instrumentation': instrumentation,
    }


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


def load_image_files(image_files):
    ids = []
    for name, imfile in image_files:
        # Run `read_image_file` sequentially to ensure `ImageEntry` is generated
        entry = _get_or_create_file_model(models.ImageFile, imfile, name=name)
        result = entry.imageentry.pk
        ids.append(result)
    return ids


def load_raster(pks, raster_dict):
    if not isinstance(pks, (list, tuple)):
        pks = [
            pks,
        ]
    # Check if an ImageSet already exists containing all of these images
    q = models.ImageSet.objects.annotate(count=Count('images')).filter(count=len(pks))
    imsets = reduce(lambda p, id: q.filter(images=id), pks, q).values()
    if len(imsets) > 0:
        # Grab first, could be N-many
        imset = models.ImageSet.objects.get(id=imsets[0]['id'])
    else:
        images = models.ImageEntry.objects.filter(pk__in=pks).all()
        imset = models.ImageSet()
        imset.save()  # Have to save before adding to ManyToManyField
        for image in images:
            imset.images.add(image)
        imset.save()
    # Make raster of that image set
    raster, created = get_or_create_no_commit(models.RasterEntry, image_set=imset)
    _save_signal(raster, created)

    # Add optional metadata
    date = raster_dict.get('acquisition_date', None)
    cloud_cover = raster_dict.get('cloud_cover', None)
    name = raster_dict.get('name', None)
    ancillary = raster_dict.get('ancillary_files', None)
    instrumentation = raster_dict.get('instrumentation', None)
    if date:
        adt = dateutil.parser.isoparser().isoparse(date)
        try:
            raster.rastermetaentry.acquisition_date = make_aware(adt)
        except ValueError:
            raster.rastermetaentry.acquisition_date = adt
        raster.rastermetaentry.save(
            update_fields=[
                'acquisition_date',
            ]
        )
    if cloud_cover:
        raster.rastermetaentry.cloud_cover = cloud_cover
        raster.rastermetaentry.save(
            update_fields=[
                'cloud_cover',
            ]
        )
    if name:
        raster.name = name
        raster.save(
            update_fields=[
                'name',
            ]
        )
    if ancillary:
        [
            raster.ancillary_files.add(_get_or_create_checksum_file_url(af, name=path))
            for path, af in ancillary
        ]
    if instrumentation:
        for im in raster.image_set.images.all():
            im.instrumentation = instrumentation
            im.save(
                update_fields=[
                    'instrumentation',
                ]
            )
    return raster


def load_raster_files(raster_dicts):
    ids = []
    count = len(raster_dicts)
    for i, rf in enumerate(raster_dicts):
        logger.info(f'Processesing raster {i+1} of {count}')
        start_time = datetime.now()
        imentries = load_image_files(rf.get('images'))
        raster = load_raster(imentries, rf)
        ids.append(raster.pk)
        logger.info('\t Loaded raster in: {}'.format(datetime.now() - start_time))
    return ids


def load_shape_files(shape_files):
    ids = []
    for shpfile in shape_files:
        entry = _get_or_create_file_model(models.GeometryArchive, shpfile)
        ids.append(entry.geometryentry.pk)
    return ids


def load_fmv_files(fmv_files):
    return [_get_or_create_file_model(models.FMVFile, fmv).id for fmv in fmv_files]


def load_kwcoco_archives(archives):
    ids = []
    for fspec, farch in archives:
        spec = _get_or_create_checksum_file(fspec)
        arch = _get_or_create_checksum_file(farch)
        ds, created = get_or_create_no_commit(
            models.KWCOCOArchive, spec_file=spec, image_archive=arch
        )
        _save_signal(ds, created)
        ids.append(ds.id)
    return ids
