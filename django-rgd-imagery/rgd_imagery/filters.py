from django.contrib.gis import forms
from django.db.models import Q, Sum
from django_filters import rest_framework as filters
from rgd.filters import SpatialEntryFilter
from rgd_imagery.models import RasterMeta


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
                num_bands=Sum('parent_raster__image_set__images__imagemeta__number_of_bands')
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
