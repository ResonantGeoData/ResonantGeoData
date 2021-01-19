from django.contrib.gis import forms
from django.contrib.gis.db.models.functions import GeometryDistance
from django.contrib.gis.measure import D
from django.core.validators import RegexValidator
from django.db.models import Q, Sum
from django_filters import rest_framework as filters

from rgd.geodata.models.common import SpatialEntry


class GeometryFilter(filters.Filter):
    field_class = forms.GeometryField


class SpatialEntryFilter(filters.FilterSet):

    q = GeometryFilter(
        help_text='A Well-known text (WKT) representation of a geometry or a GeoJSON.',
        label='WKT/GeoJSON',
        method='filter_q',
    )
    predicate = filters.ChoiceFilter(
        choices=(
            ('contains', 'contains'),
            ('crosses', 'crosses'),
            ('disjoint', 'disjoint'),
            ('equals', 'equals'),
            ('intersects', 'intersects'),
            ('overlaps', 'overlaps'),
            ('touches', 'touches'),
            ('within', 'within'),
        ),
        help_text=(
            'A named spatial predicate based on the DE-9IM. This spatial predicate will be used '
            'to filter data such that `predicate(a, b)` where `b` is the queried geometry.'
        ),
        label='Spatial predicate',
        method='filter_predicate',
    )
    relates = filters.CharFilter(
        help_text=(
            'Specify exactly how the queried geometry should relate to the data using a DE-9IM '
            'string code.'
        ),
        label='DE-9IM string code',
        max_length=9,
        method='filter_relates',
        min_length=9,
        validators=(
            RegexValidator(regex=r'^[\*012TF]{9}$', message='Enter a valid DE-9IM string code.'),
        ),
    )
    distance = filters.RangeFilter(
        help_text='The minimum/maximum distance around the queried geometry in meters.',
        label='Distance',
        method='filter_distance',
    )
    acquired = filters.IsoDateTimeFromToRangeFilter(
        field_name='acquisition_date',
        help_text='The ISO 8601 formatted date and time when data was acquired.',
        label='Acquired',
        method='filter_acquired',
    )
    created = filters.IsoDateTimeFromToRangeFilter(
        field_name='created',
        help_text='The ISO 8601 formatted date and time when data was created.',
        label='Created',
        method='filter_created',
    )
    modified = filters.IsoDateTimeFromToRangeFilter(
        field_name='modified',
        help_text='The ISO 8601 formatted date and time when data was modified.',
        label='Modified',
        method='filter_modified',
    )
    datatype = filters.ChoiceFilter(
        choices=(
            ('raster', 'raster'),
            ('fmv', 'fmv'),
            ('geometry', 'geometry'),
        ),
        help_text='The datatype to provide.',
        method='filter_datatype',
        label='Datatype',
    )
    instrumentation = filters.CharFilter(
        field_name='rastermetaentry__parent_raster__image_set__images__instrumentation',
        help_text='The instrumentation used to acquire at least one of these data.',
        label='Instrumentation',
        lookup_expr='icontains',
    )
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
    frame_rate = filters.RangeFilter(
        field_name='fmventry__fmv_file',
        fields=(forms.IntegerField(), forms.IntegerField()),
        help_text='The frame rate of the video.',
        label='Frame rate',
    )

    def filter_q(self, queryset, name, value):
        """Sort the queryset by distance to queried geometry.

        Annotates the queryset with `distance`.

        This uses the efficient KNN operation:
        https://postgis.net/docs/geometry_distance_knn.html
        """
        return queryset.annotate(distance=GeometryDistance('footprint', value)).order_by('distance')

    def filter_predicate(self, queryset, name, value):
        """Filter the spatial entries by the chosen predicate."""
        if value:
            geom = self.form.cleaned_data['q']
            return queryset.filter(**{f'footprint__{value}': geom})
        return queryset

    def filter_relates(self, queryset, name, value):
        """Filter the spatial entries by the chosen DE-9IM."""
        if value:
            geom = self.form.cleaned_data['q']
            return queryset.filter(footprint__relates=(geom, value))
        return queryset

    def filter_distance(self, queryset, name, value):
        """Filter the queryset by distance to the queried geometry.

        We may wish to use the distance in degrees later on. This is
        very taxing on the DBMS right now. The distance in degrees
        can be provided by the initial geometry query.
        """
        if value:
            geom = self.form.cleaned_data['q']
            if value.start is not None:
                queryset = queryset.filter(footprint__distance_gte=(geom, D(m=value.start)))
            if value.stop is not None:
                queryset = queryset.filter(footprint__distance_lte=(geom, D(m=value.stop)))
            return queryset

    def filter_datatype(self, queryset, name, value):
        """Filter the `SpatialEntry`s to a specific datatype."""
        if value == 'geometry':
            return queryset.filter(geometryentry__isnull=False)
        if value == 'raster':
            return queryset.filter(rastermetaentry__isnull=False)
        if value == 'fmv':
            return queryset.filter(fmventry__isnull=False)
        return queryset

    def filter_acquired(self, queryset, name, value):
        """Filter by when the data was acquired.

        There is a special where filtering by acquisition, created is also filtered
        for `RasterEntry`.
        """
        if value:
            if value.start is not None:
                queryset = queryset.filter(
                    (
                        Q(acquisition_date__gte=value)
                        | Q(rastermetaentry__parent_raster__created__gte=value)
                    )
                )
            if value.stop is not None:
                queryset = queryset.filter(
                    (
                        Q(acquisition_date__lte=value)
                        | Q(rastermetaentry__parent_raster__created__lte=value)
                    )
                )
        return queryset

    def filter_created(self, queryset, name, value):
        """Filter by when the data was created."""
        if value:
            if value.start is not None:
                queryset = queryset.filter(
                    (
                        Q(geometryentry__created__gte=value)
                        | Q(fmventry__created__gte=value)
                        | Q(rastermetaentry__parent_raster__created__gte=value)
                    )
                )
            if value.stop is not None:
                queryset = queryset.filter(
                    (
                        Q(geometryentry__created__lte=value)
                        | Q(fmventry__created__lte=value)
                        | Q(rastermetaentry__parent_raster__created__lte=value)
                    )
                )
        return queryset

    def filter_modified(self, queryset, name, value):
        """Filter by when the data was modified."""
        if value:
            if value.start is not None:
                queryset = queryset.filter(
                    (
                        Q(geometryentry__modified__gte=value)
                        | Q(fmventry__modified__gte=value)
                        | Q(rastermetaentry__parent_raster__modified__gte=value)
                    )
                )
            if value.stop is not None:
                queryset = queryset.filter(
                    (
                        Q(geometryentry__modified__lte=value)
                        | Q(fmventry__modified__lte=value)
                        | Q(rastermetaentry__parent_raster__modified__lte=value)
                    )
                )
        return queryset

    def filter_bands(self, queryset, name, value):
        """Filter by the total number of bands in the raster data.

        Annotates the queryset with `num_bands`.
        """
        if value is not None:
            queryset = queryset.annotate(
                num_bands=Sum('rastermetaentry__parent_raster__image_set__images__number_of_bands')
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
                    Q(rastermetaentry__resolution__0__gte=value.start)
                    & Q(rastermetaentry__resolution__1__gte=value.start)
                )
            if value.stop is not None:
                queryset = queryset.filter(
                    Q(rastermetaentry__resolution__0__lte=value.stop)
                    & Q(rastermetaentry__resolution__1__lte=value.stop)
                )
        return queryset

    class Meta:
        model = SpatialEntry
        fields = [
            'q',
            'predicate',
            'relates',
            'distance',
            'acquired',
            'created',
            'modified',
            'datatype',
            'instrumentation',
            'num_bands',
            'resolution',
            'frame_rate',
        ]
