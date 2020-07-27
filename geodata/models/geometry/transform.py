from celery.utils.log import get_task_logger
from django.contrib.gis.gdal import CoordTransform, SpatialReference

from ..constants import DB_SRID

logger = get_task_logger(__name__)


def transform_geometry(geometry, source_wkt):
    """Transform geometry into the database's spatial reference system."""
    logger.info('Tranforming geometry %s from %s', geometry.wkt, source_wkt)
    source = SpatialReference(source_wkt)
    dest = SpatialReference(DB_SRID)
    transform = CoordTransform(source, dest)
    geometry = geometry.transform(transform, clone=True)
    logger.info('Transformed geometry to %s', geometry.wkt)
    return geometry
