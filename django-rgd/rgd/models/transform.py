from django.contrib.gis.gdal import CoordTransform, SpatialReference
from rgd.models.constants import DB_SRID


def transform_geometry(geometry, source_wkt):
    """Transform geometry into the database's spatial reference system."""
    source = SpatialReference(source_wkt)
    dest = SpatialReference(DB_SRID)
    transform = CoordTransform(source, dest)
    return geometry.transform(transform, clone=True)
