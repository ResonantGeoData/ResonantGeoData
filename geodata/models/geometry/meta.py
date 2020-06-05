"""Meta classes that list out useful info stored by GeoDjango."""
from django.contrib.gis.geos import GeometryCollection


class GeometryCollectionMeta:
    """A meta class to point to ``GeometryCollection`` properties.

    ``django.contrib.gis.geos.GeometryCollection``

    """

    def __init__(self, collection):
        if not isinstance(collection, GeometryCollection):
            raise TypeError(
                '`GeometryCollectionMeta` only supports `GeometryCollection`. `{}` not supported.'.format(
                    type(collection)
                )
            )
        self._collection = collection

    @property
    def area(self):
        return self._collection.area

    @property
    def length(self):
        return self._collection.length

    @property
    def num_points(self):
        return self._collection.num_points

    @property
    def num_geom(self):
        return self._collection.num_geom

    @property
    def extent(self):
        return self._collection.extent
