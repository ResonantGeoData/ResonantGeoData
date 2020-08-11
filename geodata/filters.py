from django_filters import rest_framework as filters
from rest_framework_gis.filters import GeometryFilter
from rest_framework_gis.filterset import GeoFilterSet

from . import models


class SpatialEntryFilter(GeoFilterSet):
    footprint = GeometryFilter(field_name='footprint')
    outline = GeometryFilter(field_name='outline')

    class Meta:
        model = models.SpatialEntry
        fields = '__all__'


class RasterEntryFilter(SpatialEntryFilter):
    origin = filters.NumberFilter(field_name='origin')
    extent = filters.NumberFilter(field_name='extent')
    resolution = filters.NumberFilter(field_name='resolution')
    metadata = filters.CharFilter(field_name='metadata')
    transform = filters.NumberFilter(field_name='transform')

    class Meta:
        model = models.RasterEntry
        fields = '__all__'


class GeometryEntryFilter(SpatialEntryFilter):
    data = GeometryFilter(field_name='data')

    class Meta:
        model = models.GeometryEntry
        fields = '__all__'
