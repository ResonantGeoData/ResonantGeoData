from django_filters import rest_framework as filters
from django.contrib.postgres import fields as pg_fields
from rest_framework import generics
from rest_framework_gis.filterset import GeoFilterSet
from rest_framework_gis.filters import GeometryFilter

from . import models


class JSONFilter(filters.Filter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        return qs.filter(**value)



class SpatialEntryFilter(GeoFilterSet):
	footprint = GeometryFilter(field_name='footprint')
	class Meta:
		model = models.SpatialEntry
		fields = '__all__'


class RasterEntryFilter(SpatialEntryFilter):
	outline = filters.NumberFilter(field_name='outline')
	origin = filters.NumberFilter(field_name='origin')
	extent = filters.NumberFilter(field_name='extent')
	resolution = filters.NumberFilter(field_name='resolution')
	metadata = filters.CharFilter(field_name='metadata')
	transform = filters.NumberFilter(field_name='transform')
	class Meta:
		model = models.RasterEntry
		fields = '__all__'