"""Helper methods for creating a geometry entries from uploaded files."""
from glob import glob
import os
import tempfile
import zipfile

from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import GeometryCollection, GEOSGeometry, Polygon
from django.core.exceptions import ValidationError
import fiona
from shapely.geometry import shape
from shapely.wkb import dumps

from .base import GeometryArchive, GeometryEntry
from .transform import transform_geometry

logger = get_task_logger(__name__)


def read_geometry_archive(archive_id):
    """Read an archive of a single shapefile (and associated) files.

    This will load zipped archives of shape files and create entries
    for a single shapefile (basename of files).

    A single shapefile will consist of a collection of one or many features
    of varying types. We produce a single ``GeometryCollection`` of those
    data. Hence, we associate a single shapefile with a single
    ``GeometryCollection``.

    We may need to do more checks/validation to make sure the user only
    added a single shape file or provide a more explicit upload interface
    where they upload the ``shp``, ``dbf``, etc. files individually and
    we assert that they match.

    """
    archive = GeometryArchive.objects.get(id=archive_id)

    # TODO: add a setting like this:
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    tmpdir = tempfile.mkdtemp(dir=workdir)

    with archive.file.open() as archive_file_obj:
        logger.info(f'The geometry archive: {archive.file}')

        # Unzip the contents to the working dir
        with zipfile.ZipFile(archive_file_obj, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)

    msg = 'There must be one and only one shapefile in the archive. Found ({})'
    shape_files = glob(os.path.join(tmpdir, '*.shp'))
    if len(shape_files) > 1:
        raise ValidationError(msg.format(len(shape_files)))
    elif len(shape_files) == 0:
        shape_files = glob(os.path.join(tmpdir, '**/*.shp'))
        if len(shape_files) != 1:
            raise ValidationError(msg.format(len(shape_files)))
    shape_file = shape_files[0]

    # load each shapefile using fiona
    shapes = fiona.open(shape_file)

    # create a model entry for that shapefile
    geometry_query = GeometryEntry.objects.filter(geometry_archive=archive)
    if len(geometry_query) < 1:
        geometry_entry = GeometryEntry()
        # geometry_entry.creator = archive.creator
        geometry_entry.name = archive.name
        geometry_entry.geometry_archive = archive
    elif len(geometry_query) == 1:
        geometry_entry = geometry_query.first()
    else:
        # This should never happen because it is a foreign key
        raise RuntimeError('multiple geometry entries found for this file.')  # pragma: no cover

    # geometry_entry.modifier = archive.modifier

    shapes.meta  # TODO: dump this JSON into the model entry

    crs_wkt = shapes.meta['crs_wkt']
    logger.info(f'Geometry crs_wkt: {crs_wkt}')
    spatial_ref = SpatialReference(crs_wkt)
    logger.info(f'Geometry SRID: {spatial_ref.srid}')

    collection = []
    for item in shapes:
        geom = shape(item['geometry'])  # not optimal?
        # TODO: check this
        collection.append(
            transform_geometry(
                GEOSGeometry(memoryview(dumps(geom, srid=spatial_ref.srid)), srid=spatial_ref.srid),
                crs_wkt,
            )
        )

    geometry_entry.data = GeometryCollection(*collection)
    geometry_entry.footprint = geometry_entry.data.convex_hull
    bounds = geometry_entry.footprint.extent
    coords = [
        (bounds[0], bounds[3]),
        (bounds[2], bounds[3]),
        (bounds[2], bounds[1]),
        (bounds[0], bounds[1]),
        (bounds[0], bounds[3]),  # Close the loop
    ]
    geometry_entry.outline = Polygon(coords)

    geometry_entry.save()

    return True
