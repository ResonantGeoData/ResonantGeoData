"""Helper methods for creating a ``GDALRaster`` entry from a raster file."""
from celery.utils.log import get_task_logger
from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import Polygon
import numpy as np
from osgeo import gdal
import rasterio

from rgd.utility import _field_file_to_local_path
from .base import BandMetaEntry, ConvertedRasterFile, RasterEntry
from .ifiles import RasterFile
from ..common import _ReaderRoutine
from ..geometry.transform import transform_geometry

logger = get_task_logger(__name__)


MAX_LOAD_SHAPE = (4000, 4000)


def convex_hull(points):
    from scipy.spatial import ConvexHull

    hull = ConvexHull(points)

    boundary = points[hull.vertices]
    # Close the loop
    boundary = np.append(boundary, boundary[0][None], axis=0)

    return boundary


def get_valid_data_footprint(src, band_num):
    """Fetch points for the footprint polygon of the valid data.

    Must specify band of the raster to evaluate.

    src is an open dataset with rasterio

    Returns a numpy array of the bounadry points in a closed polygon.

    """
    # Determine mask resolution to prevent loading massive imagery
    shape = tuple(np.min([src.shape, MAX_LOAD_SHAPE], axis=0))

    msk = src.read_masks(band_num, out_shape=shape)

    a = (np.arange(msk.shape[1]) * src.res[1]) + (src.bounds.left + (src.res[1] / 2.0))
    b = ((np.arange(msk.shape[0]) * src.res[0]) + (src.bounds.bottom + (src.res[0] / 2.0)))[::-1]
    xx, yy = np.meshgrid(a, b[::-1])
    ids = np.argwhere(msk.ravel()).ravel()

    x = xx.ravel()[ids]
    y = yy.ravel()[ids]
    points = np.c_[x, y]

    return convex_hull(points)


class RasterEntryReader(_ReaderRoutine):
    """Raster ingestion routine.

    This helper class will open a raster file from ``RasterFile`` and create a
    ``RasterEntry`` and collection of ``BandMetaEntry`` entries.

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
        with _field_file_to_local_path(self.rfe.file) as file_path:

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
            self.raster_entry.creator = self.rfe.creator
            self.raster_entry.modifier = self.rfe.modifier

            with rasterio.open(file_path) as src:
                self.raster_entry.number_of_bands = src.count
                self.raster_entry.driver = src.driver
                self.raster_entry.crs = src.crs.to_proj4()
                self.raster_entry.origin = [src.bounds.left, src.bounds.bottom]
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

                coords = np.array(
                    (
                        (src.bounds.left, src.bounds.top),
                        (src.bounds.right, src.bounds.top),
                        (src.bounds.right, src.bounds.bottom),
                        (src.bounds.left, src.bounds.bottom),
                        (src.bounds.left, src.bounds.top),  # Close the loop
                    )
                )

                spatial_ref = SpatialReference(src.crs.to_wkt())
                logger.info(f'Raster footprint SRID: {spatial_ref.srid}')
                # This will convert the Polygon to the DB's SRID
                self.raster_entry.outline = transform_geometry(
                    Polygon(coords, srid=spatial_ref.srid), src.crs.to_wkt()
                )
                try:
                    # Only implement for first band for now
                    vcoords = get_valid_data_footprint(src, 1)
                    self.raster_entry.footprint = transform_geometry(
                        Polygon(vcoords, srid=spatial_ref.srid), src.crs.to_wkt()
                    )
                except Exception as e:  # TODO: be more clever about this
                    logger.info(f'Issue computing convex hull of non-null data: {e}')
                    self.raster_entry.footprint = self.raster_entry.outline

                # These are things I couldn't figure out how to get with gdal directly
                dtypes = src.dtypes
                interps = src.colorinterp

            # Rasterio is no longer open... using gdal directly:
            gsrc = gdal.Open(str(file_path))  # Have to cast Path to str
            self.band_entries = []
            n = gsrc.RasterCount
            if n != self.raster_entry.number_of_bands:
                # Sanity check
                self.raster_entry.number_of_bands
            for i in range(n):
                gdal_band = gsrc.GetRasterBand(i + 1)  # off by 1 indexing
                band_meta = BandMetaEntry()
                band_meta.parent_raster = self.raster_entry
                band_meta.description = gdal_band.GetDescription()
                band_meta.nodata_value = gdal_band.GetNoDataValue()
                band_meta.creator = self.rfe.creator
                band_meta.modifier = self.rfe.modifier
                try:
                    band_meta.dtype = dtypes[i]
                except IndexError:
                    pass
                bmin, bmax, mean, std = gdal_band.GetStatistics(True, True)
                band_meta.min = bmin
                band_meta.max = bmax
                band_meta.mean = mean
                band_meta.std = std

                try:
                    band_meta.interpretation = interps[i].name
                except IndexError:
                    pass

                # Keep track
                self.band_entries.append(band_meta)

        return True

    def _save_entries(self):
        """Save entries."""
        self.raster_entry.save()
        for band in self.band_entries:
            band.save()
