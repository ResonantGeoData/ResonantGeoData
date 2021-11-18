from dateutil.parser import parse as datetimeparse
from django.contrib.gis import forms
from django.contrib.gis.geos import Polygon
from django_filters import rest_framework as filters
from rgd.models import SpatialEntry


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class NumberCSVFilter(filters.BaseCSVFilter, filters.NumberFilter):
    pass


class GeometryFilter(filters.Filter):
    field_class = forms.GeometryField
    # Ensures GeoJSON objects are converted to correct SRID
    field_class.widget.map_srid = 4326


class STACSimpleFilter(filters.FilterSet):
    bbox = NumberCSVFilter(
        help_text=(
            'Only features that have a geometry that intersects the bounding box are selected. '
            'The bounding box is provided as four comma separated numbers.'
        ),
        label='Bounding Box',
        method='filter_bbox',
    )
    intersects = GeometryFilter(
        help_text='A GeoJSON to filter against.',
        label='GeoJSON',
        method='filter_intersects',
    )
    ids = NumberInFilter(
        help_text='Array of Item ids to return.',
        label='IDs.',
        field_name='pk',
        lookup_expr='in',
    )
    collections = NumberInFilter(
        help_text='Array of Collection IDs to limit results to.',
        label='Collections.',
        field_name='parent_raster__image_set__images__file__collection',
        lookup_expr='in',
    )
    datetime = filters.CharFilter(
        help_text=(
            'Either a date-time or an interval, open or closed. Date and time expressions adhere to '
            'RFC 3339. Open intervals are expressed using double-dots.'
            'string code.'
        ),
        label='Datetime',
        method='filter_datetime',
    )

    def filter_bbox(self, queryset, name, value):
        if value:
            bbox = [int(i) for i in value]
            geom = Polygon.from_bbox(bbox)
            return queryset.filter(footprint__intersects=geom)
        return queryset

    def filter_intersects(self, queryset, name, value):
        if value:
            return queryset.filter(footprint__intersects=value)
        return queryset

    def filter_datetime(self, queryset, name, value):
        if value:
            split_datetime = value.split('/')
            if len(split_datetime) == 1:
                obj = datetimeparse(split_datetime[0])
                return queryset.filter(acquisition_date__time=obj)
            else:
                start = split_datetime[0]
                end = split_datetime[1]
                if start != '..':
                    obj = datetimeparse(start)
                    queryset = queryset.filter(acquisition_date__time__gte=obj)
                if end != '..':
                    obj = datetimeparse(end)
                    queryset = queryset.filter(acquisition_date__time__lte=obj)
        return queryset

    class Meta:
        model = SpatialEntry
        fields = [
            'bbox',
            'intersects',
            'ids',
            'collections',
            'datetime',
        ]
