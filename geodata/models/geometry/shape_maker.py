from django.contrib.gis.gdal import SpatialReference
from django.contrib.gis.geos import GEOSGeometry
from osgeo import ogr
from osgeo.osr import CoordinateTransformation, SpatialReference as SpatRef2

from ..constants import DB_SRID


def transform_geometry(geometry, source_wkt):
    g = ogr.Geometry(wkt=geometry.wkt)
    source = SpatRef2(source_wkt)
    dest = SpatRef2(SpatialReference(DB_SRID).wkt)
    g.Transform(CoordinateTransformation(source, dest))
    return GEOSGeometry(g.ExportToWkt())
