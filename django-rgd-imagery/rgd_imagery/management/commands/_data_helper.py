from datetime import datetime
import json
import logging

import dateutil.parser
from django.contrib.gis.geos import GEOSGeometry
from django.utils.timezone import make_aware
from rgd.datastore import datastore
from rgd.management.commands._data_helper import (
    _get_or_create_checksum_file,
    _get_or_create_checksum_file_url,
    _get_or_create_file_model,
    _save_signal,
)
from rgd.utility import get_or_create_no_commit
from rgd_imagery import models
from rgd_imagery.tasks import etl
from shapely.geometry import shape
from shapely.wkb import dumps

logger = logging.getLogger(__name__)


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


def load_images(images):
    ids = []
    for name, imfile in images:
        # Run `load_image` sequentially to ensure `Image` is generated
        entry = _get_or_create_file_model(models.Image, imfile, name=name)
        ids.append(entry.pk)
    return ids


def load_raster(pks, raster_dict, footprint=False):
    if not isinstance(pks, (list, tuple)):
        pks = [
            pks,
        ]
    imset, _ = models.get_or_create_image_set(pks)
    # Make raster of that image set
    raster, created = get_or_create_no_commit(models.Raster, image_set=imset)
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
            raster.rastermeta.acquisition_date = make_aware(adt)
        except ValueError:
            raster.rastermeta.acquisition_date = adt
        raster.rastermeta.save(
            update_fields=[
                'acquisition_date',
            ]
        )
    if cloud_cover:
        raster.rastermeta.cloud_cover = cloud_cover
        raster.rastermeta.save(
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
        raster.rastermeta.instrumentation = instrumentation
        raster.rastermeta.save(
            update_fields=[
                'instrumentation',
            ]
        )
    if footprint:
        etl.populate_raster_footprint(raster.id)
    return raster


def load_raster_files(raster_dicts, footprint=False):
    ids = []
    count = len(raster_dicts)
    for i, rf in enumerate(raster_dicts):
        logger.info(f'Processesing raster {i+1} of {count}')
        start_time = datetime.now()
        imentries = load_images(rf.get('images'))
        raster = load_raster(imentries, rf, footprint=footprint)
        ids.append(raster.pk)
        logger.info('\t Loaded raster in: {}'.format(datetime.now() - start_time))
    return ids


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


def load_spatial_image_sets(image_sets):
    for value in image_sets:
        image_files, loc_file = value
        path = datastore.fetch(loc_file)
        # Load JSON image
        with open(path, 'r') as f:
            geom = shape(json.loads(f.read())['geometry'])
        feature = GEOSGeometry(memoryview(dumps(geom)))
        # Load image entries
        image_ids = load_images(list(zip([None] * len(image_files), image_files)))
        imset, _ = models.get_or_create_image_set(image_ids)
        # Make an ImageSetSpatial
        imset_spatial, _ = get_or_create_no_commit(models.ImageSetSpatial, image_set=imset)
        imset_spatial.footprint = feature
        imset_spatial.outline = feature.convex_hull
        imset_spatial.save()
