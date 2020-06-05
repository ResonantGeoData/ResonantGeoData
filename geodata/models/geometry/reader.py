"""Helper methods for creating a geometry entries from uploaded files.
"""
import os
from glob import glob
import zipfile

from celery.utils.log import get_task_logger
from django.contrib.gis.gdal import GDALRaster, OGRGeometry
from django.contrib.gis.geos import GEOSGeometry, GeometryCollection
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

import fiona
from shapely.geometry import shape
from shapely.wkb import dumps

from .base import GeometryEntry, GeometryArchive
from ..constants import DB_SRID
from ..common import _ReaderRoutine

logger = get_task_logger(__name__)


class GeometryArchiveReader(_ReaderRoutine):
    """
    """

    def _read_files(self):
        """This will load zipped archives of shape files and create entries
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
        file_path = self.archive.archive_file.name
        logger.info(f"The geometry archive: {file_path}")

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
        if self.archive.geometry_entry is None:
            self.archive.geometry_entry = GeometryEntry()

        shapes.meta  # TODO: dump this JSON into the model entry

        collection = []
        for item in shapes:
            geom = shape(item['geometry'])  # not optimal?
            collection.append(GEOSGeometry(memoryview(dumps(geom, srid=DB_SRID))))
        self.archive.geometry_entry.data = GeometryCollection(*collection)

        return True

    def _save_entries(self):
        self.archive.geometry_entry.save()
        self.archive.save(
            update_fields=['geometry_entry',]
        )
        return
