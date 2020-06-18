"""Helper methods for creating a ``GDALRaster`` entry from a raster file."""
from celery.utils.log import get_task_logger
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import Polygon
import rasterio

from rgd.utility import _field_file_to_local_path
from .base import BandMetaEntry, ConvertedRasterFile, RasterEntry, RasterFile
from ..common import _ReaderRoutine

logger = get_task_logger(__name__)


class RasterEntryReader(_ReaderRoutine):
    """Raster injestion routine.

    This helper class will open a raster file and create the ``GDALRaster``
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
        """Load raster data files and create a ``RasterEntry``.

        This function will need to handle a lot of scenarios for how
        the raster file is passed and where it is stored.

        """
        # Fetch the raster file this Layer corresponds to
        self.rfe = RasterFile.objects.get(id=self.model_id)
        with _field_file_to_local_path(self.rfe.raster_file) as file_path:

            logger.info(f'The raster file path: {file_path}')

            raster_query = RasterEntry.objects.filter(raster_file=self.rfe)
            if len(raster_query) < 1:
                self.raster_entry = RasterEntry()
                self.raster_entry.name = self.rfe.name
            elif len(raster_query) == 1:
                self.raster_entry = raster_query.first()
                # Clear out associated entries because they could be invalid
                BandMetaEntry.objects.filter(parent_raster=self.raster_entry).delete()
                ConvertedRasterFile.objects.filter(source_raster=self.raster_entry).delete()
            else:
                # This should never happen because it is a foreign key
                raise RuntimeError('multiple raster entries found for this file.')

            self.raster_entry.raster_file = self.rfe

            with rasterio.open(file_path) as src:
                self.raster_entry.number_of_bands = src.count
                self.raster_entry.driver = src.driver
                self.raster_entry.crs = src.crs.to_proj4()
                self.raster_entry.origin = [src.bounds.left, src.bounds.top]
                self.raster_entry.extent = [
                    src.bounds.left,
                    src.bounds.bottom,
                    src.bounds.right,
                    src.bounds.top,
                ]
                self.raster_entry.resolution = src.res
                self.raster_entry.height = src.shape[0]
                self.raster_entry.width = src.shape[1]
                self.raster_entry.transform = src.transform.to_gdal()  # TODO: check this
                # A catch-all metadata feild:
                # TODO: self.raster_entry.metadata =

                # thumbnail = RasterEntryReader.create_thumbnail(src)
                # self.raster_entry.thumbnail.save('thumbnail.jpg', thumbnail, save=True)

                coords = (
                    (src.bounds.left, src.bounds.top),
                    (src.bounds.right, src.bounds.top),
                    (src.bounds.right, src.bounds.bottom),
                    (src.bounds.left, src.bounds.bottom),
                    (src.bounds.left, src.bounds.top),  # Close the loop
                )

                spatial_ref = SpatialReference(src.crs.to_wkt())
                logger.info(f'Raster footprint SRID: {spatial_ref.srid}')
                # This will convert the Polygon to the DB's SRID
                self.raster_entry.footprint = Polygon(coords, srid=spatial_ref.srid)

                # TODO: now create a `BandMetaEntry` entry for each band
                #       this will collect statistics on the bands
                self.band_entries = []
                for i in range(src.count):
                    band_meta = BandMetaEntry()
                    band_meta.parent_raster = self.raster_entry
                    try:
                        band_meta.description = src.descriptions[i]
                    except IndexError:
                        pass
                    try:
                        band_meta.nodata_value = src.nodatavals[i]
                    except IndexError:
                        pass
                    try:
                        band_meta.dtype = src.dtypes[i]
                    except IndexError:
                        pass
                    # TODO: Compute statistics: min, max, mean, std
                    #       We'd have to load the bands into memroy...
                    #       might not be good.

                    # Keep track
                    self.band_entries.append(band_meta)

        return True

    def _save_entries(self):
        """Save entries."""
        self.raster_entry.save()
        for band in self.band_entries:
            band.save()
        return
