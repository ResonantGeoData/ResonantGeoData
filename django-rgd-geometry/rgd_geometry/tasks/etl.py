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
from rgd.models.transform import transform_geometry
from rgd.utility import get_or_create_no_commit
from rgd_geometry.models import Geometry, GeometryArchive
from shapely.geometry import shape
from shapely.wkb import dumps

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
    with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
        with archive.file.yield_local_path() as archive_path:
            logger.info(f'The geometry archive: {archive_path}')

            # Unzip the contents to the working dir
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
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
        with fiona.open(shape_file) as shapes:
            geometry_entry, created = get_or_create_no_commit(
                Geometry, defaults=dict(name=archive.file.name), geometry_archive=archive
            )

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
                        GEOSGeometry(
                            memoryview(dumps(geom, srid=spatial_ref.srid)), srid=spatial_ref.srid
                        ),
                        crs_wkt,
                    )
                )

    geometry_entry.data = GeometryCollection(*collection)
    geometry_entry.footprint = geometry_entry.data.convex_hull
    bounds = geometry_entry.footprint.extent  # (xmin, ymin, xmax, ymax)
    coords = [
        (bounds[0], bounds[3]),  # (xmin, ymax)
        (bounds[2], bounds[3]),  # (xmax, ymax)
        (bounds[2], bounds[1]),  # (xmax, ymin)
        (bounds[0], bounds[1]),  # (xmin, ymin)
        (bounds[0], bounds[3]),  # Close the loop
    ]
    geometry_entry.outline = Polygon(coords)

    geometry_entry.save()

    return True
