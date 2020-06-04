"""Helper methods for creating a ``GDALRaster`` entry from a raster file.
"""
import os

from celery.utils.log import get_task_logger
from django.contrib.gis.gdal import GDALRaster, OGRGeometry
from django.core.files.base import ContentFile

# import io
# from PIL import Image
import rasterio

from .base import RasterEntry, RasterFile
from ..common import _ReaderRoutine

logger = get_task_logger(__name__)


class RasterEntryReader(_ReaderRoutine):
    """This helper class will open a raster file and create the ``GDALRaster``
    for the ``RasterEntry``'s raster property.

    """

    # @staticmethod
    # def create_thumbnail(src):
    #     oview = int(max(src.height, src.width) * 0.1) or 1
    #     thumbnail = src.read(1, out_shape=(1, int(src.height // oview), int(src.width // oview)))
    #
    #     buf = io.BytesIO()
    #     thumbnail.save(buf, format='JPEG')
    #     byte_im = buf.getvalue()
    #     return ContentFile(byte_im)

    def _read_files(self):
        """TODO: this function will need to handle a lot of scenarios for how
        the raster file is passed and where it is stored. In most cases, a
        local copy will need to be created...
        """
        # Fetch the raster file this Layer corresponds to
        self.rfe = RasterFile.objects.get(id=self.model_id)
        file_path = self.rfe.raster_file.name
        # file_path = os.path.join(self.tmpdir, os.path.basename(self.rfe.raster_file.name))
        # local_file = open(file_path, 'wb')
        # for chunk in self.rfe.raster_file.chunks():
        #     local_file.write(chunk)
        # local_file.close()

        logger.info(f"The raster file path: {file_path}")

        # TODO: make sure CRS matched SRID in DB
        if self.rfe.raster_entry is None:
            self.rfe.raster_entry = RasterEntry()
        self.rfe.raster_entry.raster = GDALRaster(file_path, write=True)

        with rasterio.open(file_path) as src:
            self.rfe.raster_entry.resolution = src.res[0], src.res[1]
            self.rfe.raster_entry.n_bands = src.count
            # thumbnail = RasterEntryReader.create_thumbnail(src)
            # self.rfe.raster_entry.thumbnail.save('thumbnail.jpg', thumbnail, save=True)

        return True

    def _save_entries(self):
        """This will populate the ``RasterField`` property of the layer.
        """
        # Now actually save the raster entry!
        self.rfe.raster_entry.save()
        self.rfe.save(update_fields=[
            'raster_entry'
        ])
        return
