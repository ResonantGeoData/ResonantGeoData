from functools import reduce
import os

import dateutil.parser
from django.db.models import Count
from django.utils.timezone import make_aware

from rgd.geodata import models, tasks
from rgd.geodata.datastore import datastore, registry
from rgd.geodata.models.imagery.etl import populate_raster_entry, read_image_file
from rgd.utility import get_or_create_no_commit, safe_urlopen


def _get_or_download_checksum_file(name):
    # Check if there is already an image file with this sha or URL
    #  to avoid duplicating data
    try:
        with safe_urlopen(name) as _:
            pass  # HACK: see if URL first
        try:
            file_entry = models.ChecksumFile.objects.get(url=name)
        except models.ChecksumFile.DoesNotExist:
            file_entry = models.ChecksumFile()
            file_entry.url = name
            file_entry.type = models.FileSourceType.URL
            file_entry.save()
    except ValueError:
        sha = registry[name].split(':')[1]  # NOTE: assumes sha512
        try:
            file_entry = models.ChecksumFile.objects.get(checksum=sha)
        except models.ChecksumFile.DoesNotExist:
            path = datastore.fetch(name)
            file_entry = models.ChecksumFile()
            file_entry.name = name
            file_entry.file.save(os.path.basename(path), open(path, 'rb'))
            file_entry.type = models.FileSourceType.FILE_FIELD
            file_entry.save()
            tasks.task_checksum_file_post_save.delay(file_entry.id)
    return file_entry


def _get_or_create_file_model(model, name, skip_signal=False):
    # For models that point to a `ChecksumFile`
    file_entry = _get_or_download_checksum_file(name)
    # No commit in case we need to skip the signal
    entry, created = get_or_create_no_commit(model, file=file_entry)
    # In case the last population failed
    if skip_signal:
        entry.skip_signal = True
    if created or entry.status != models.mixins.Status.SUCCEEDED:
        entry.save()
    return entry


def load_image_files(image_files):
    ids = []
    for imfile in image_files:
        if isinstance(imfile, (list, tuple)):
            result = load_image_files(imfile)
        else:
            # Run `read_image_file` sequentially to ensure `ImageEntry` is generated
            entry = _get_or_create_file_model(models.ImageFile, imfile, skip_signal=True)
            read_image_file(entry)
            result = entry.imageentry.pk
        ids.append(result)
    return ids


def load_raster_files(raster_files, dates=None, names=None):

    if isinstance(raster_files, dict):
        files = []
        dates = []
        names = []
        cloud_cover = []
        for name, rf in raster_files.items():
            files.append([rf['R'], rf['G'], rf['B']])
            dates.append(rf['acquisition'])
            names.append(name)
            cloud_cover.append(rf['cloud_cover'])
        raster_files = files

    ids = []
    for i, rf in enumerate(raster_files):
        imentries = load_image_files(
            [
                rf,
            ]
        )
        for pks in imentries:
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
            raster.skip_signal = True
            raster.save()
            if raster.status != models.mixins.Status.SUCCEEDED:
                # Run init task in sequence to create associated rastermetaentry
                populate_raster_entry(raster)
            if dates:
                adt = dateutil.parser.isoparser().isoparse(dates[i])
                raster.rastermetaentry.acquisition_date = make_aware(adt)
                raster.rastermetaentry.cloud_cover = cloud_cover[i]
                raster.rastermetaentry.save(
                    update_fields=[
                        'acquisition_date',
                        'cloud_cover',
                    ]
                )
                raster.name = names[i]
                raster.save(
                    update_fields=[
                        'name',
                    ]
                )
            ids.append(raster.pk)
    return ids


def load_shape_files(shape_files):
    ids = []
    for shpfile in shape_files:
        entry = _get_or_create_file_model(models.GeometryArchive, shpfile)
        ids.append(entry.geometryentry.pk)
    return ids


def load_fmv_files(fmv_files):
    raise NotImplementedError('FMV ETL with Docker is still broken.')


def load_kwcoco_archives(archives):
    ids = []
    for fspec, farch in archives:
        spec = _get_or_download_checksum_file(fspec)
        arch = _get_or_download_checksum_file(farch)
        ds, _ = get_or_create_no_commit(models.KWCOCOArchive, spec_file=spec, image_archive=arch)
        ds.save()
        ids.append(ds.id)
    return ids
