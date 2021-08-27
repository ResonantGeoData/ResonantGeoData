from django.contrib.gis import forms
from django.contrib.gis.db.models.functions import GeometryDistance
from django.contrib.gis.measure import D
from django.core.validators import RegexValidator
from django.db.models import F
from django_filters import rest_framework as filters
from rgd.models import SpatialEntry


class GeometryFilter(filters.Filter):
    field_class = forms.GeometryField
    # Ensures GeoJSON objects are converted to correct SRID
    field_class.widget.map_srid = 4326


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
    )
    instrumentation = filters.CharFilter(
        field_name='instrumentation',
        help_text='The instrumentation used to acquire at least one of these data.',
        label='Instrumentation',
        lookup_expr='icontains',
    )

    time_of_day = filters.TimeRangeFilter(
        help_text='The minimum/maximum times during the day the records were acquired.',
        label='Time of Day',
        method='filter_time_of_day',
    )

    @property
    def _geometry(self):
        return self.form.cleaned_data['q']

    @property
    def _has_geom(self):
        return self._geometry is not None

    def filter_q(self, queryset, name, value):
        """Sort the queryset by distance to queried geometry.

        Annotates the queryset with `distance`.

        This uses the efficient KNN operation:
        https://postgis.net/docs/geometry_distance_knn.html
        """
        if value:
            queryset = queryset.annotate(distance=GeometryDistance('footprint', value)).order_by(
                'distance'
            )
        return queryset

    def filter_predicate(self, queryset, name, value):
        """Filter the spatial entries by the chosen predicate."""
        if value and self._has_geom:
            queryset = queryset.filter(**{f'footprint__{value}': self._geometry})
        return queryset

    def filter_relates(self, queryset, name, value):
        """Filter the spatial entries by the chosen DE-9IM."""
        if value and self._has_geom:
            queryset = queryset.filter(footprint__relates=(self._geometry, value))
        return queryset

    def filter_distance(self, queryset, name, value):
        """Filter the queryset by distance to the queried geometry.

        We may wish to use the distance in degrees later on. This is
        very taxing on the DBMS right now. The distance in degrees
        can be provided by the initial geometry query.
        """
        if value and self._has_geom:
            geom = self._geometry
            if value.start is not None:
                queryset = queryset.filter(footprint__distance_gte=(geom, D(m=value.start)))
            if value.stop is not None:
                queryset = queryset.filter(footprint__distance_lte=(geom, D(m=value.stop)))
        return queryset

    def filter_time_of_day(self, queryset, name, value):
        """Filter the queryset by time of day acquired.

        Use case: find all rasters acquired between 8am and 4pm
        for all days in the acquired date range (i.e. only daytime imagery)
        """
        if value is not None:
            queryset = queryset.annotate(time_of_day=F('acquisition_date__time'))
            if value.start is not None:
                queryset = queryset.filter(time_of_day__gte=value.start)
            if value.stop is not None:
                queryset = queryset.filter(time_of_day__lte=value.stop)
        return queryset

    class Meta:
        model = SpatialEntry
        fields = [
            'q',
            'predicate',
            'relates',
            'distance',
            'acquired',
            'instrumentation',
            'time_of_day',
        ]
