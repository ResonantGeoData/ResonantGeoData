from dateutil.parser import parse as datetimeparse
from django.contrib.gis import forms
from django.contrib.gis.geos import Polygon
from django.db.models import Count, Q
from django_filters import rest_framework as filters
from rgd.filters import SpatialEntryFilter
from rgd.models import SpatialEntry
from rgd_imagery.models import RasterMeta


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class NumberCSVFilter(filters.BaseCSVFilter, filters.NumberFilter):
    pass


class GeometryFilter(filters.Filter):
    field_class = forms.GeometryField
    # Ensures GeoJSON objects are converted to correct SRID
    field_class.widget.map_srid = 4326


class RasterMetaFilter(SpatialEntryFilter):

    num_bands = filters.RangeFilter(
        fields=(forms.IntegerField(), forms.IntegerField()),
        help_text='The number of bands in the raster.',
        method='filter_bands',
        label='Number of bands',
    )
    resolution = filters.RangeFilter(
        fields=(forms.IntegerField(), forms.IntegerField()),
        help_text='The resolution of the raster.',
        label='Resolution',
        method='filter_resolution',
    )
    cloud_cover = filters.RangeFilter(
        field_name='cloud_cover',
        fields=(forms.FloatField(), forms.FloatField()),
        help_text='The cloud coverage of the raster.',
        label='Cloud cover',
    )

    def filter_bands(self, queryset, name, value):
        """Filter by the total number of bands in the raster data.

        Annotates the queryset with `num_bands`.
        """
        if value is not None:
            queryset = queryset.annotate(
                num_bands=Count('parent_raster__image_set__images__bandmeta')
            )
            if value.start is not None:
                queryset = queryset.filter(num_bands__gte=value.start)
            if value.stop is not None:
                queryset = queryset.filter(num_bands__lte=value.stop)
        return queryset

    def filter_resolution(self, queryset, name, value):
        """Filter by the resolution in the raster data."""
        if value is not None:
            if value.start is not None:
                queryset = queryset.filter(
                    Q(resolution__0__gte=value.start) & Q(resolution__1__gte=value.start)
                )
            if value.stop is not None:
                queryset = queryset.filter(
                    Q(resolution__0__lte=value.stop) & Q(resolution__1__lte=value.stop)
                )
        return queryset

    class Meta:
        model = RasterMeta
        fields = [
            'num_bands',
            'resolution',
            'cloud_cover',
        ]


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
