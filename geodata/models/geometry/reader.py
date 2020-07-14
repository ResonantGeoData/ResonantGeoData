"""Helper methods for creating a geometry entries from uploaded files."""
from glob import glob
import os
import zipfile

from celery.utils.log import get_task_logger
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import GeometryCollection, GEOSGeometry
from django.core.exceptions import ValidationError
import fiona
from shapely.geometry import shape
from shapely.wkb import dumps

from rgd.utility import _field_file_to_local_path
from .base import GeometryArchive, GeometryEntry
from ..common import _ReaderRoutine


logger = get_task_logger(__name__)


class GeometryArchiveReader(_ReaderRoutine):
    """Shapefile geometry injestion routine."""

    def _read_files(self):
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
        self.archive = GeometryArchive.objects.get(id=self.model_id)
        with _field_file_to_local_path(self.archive.file) as file_path:
            logger.info(f'The geometry archive: {file_path}')

            # Unzip the contents to the working dir
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(self.tmpdir)

        shape_files = glob(os.path.join(self.tmpdir, '*.shp'))
        if len(shape_files) != 1:
            raise ValidationError('There must be one and only one shapefile in the archive.')
        shape_file = shape_files[0]

        # load each shapefile using fiona
        shapes = fiona.open(shape_file)

        # create a model entry for that shapefile
        geometry_query = GeometryEntry.objects.filter(geometry_archive=self.archive)
        if len(geometry_query) < 1:
            self.geometry_entry = GeometryEntry()
            self.geometry_entry.creator = self.archive.creator
            self.geometry_entry.name = self.archive.name
            self.geometry_entry.geometry_archive = self.archive
        elif len(geometry_query) == 1:
            self.geometry_entry = geometry_query.first()
        else:
            # This should never happen because it is a foreign key
            raise RuntimeError('multiple geometry entries found for this file.')

        self.geometry_entry.modifier = self.archive.modifier

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
                GEOSGeometry(memoryview(dumps(geom, srid=spatial_ref.srid)), srid=spatial_ref.srid)
            )

        self.geometry_query.data = GeometryCollection(*collection)
        self.geometry_query.footprint = self.geometry_query.data.convex_hull

        return True

    def _save_entries(self):
        self.geometry_query.save()
        self.archive.save(update_fields=['geometry_entry'])
        return
