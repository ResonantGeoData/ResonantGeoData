from django.contrib.gis import forms
from django_filters import rest_framework as filters
from rgd.filters import SpatialEntryFilter
from rgd_3d.models import Mesh3DSpatial


class Mesh3DFilter(SpatialEntryFilter):

    heading = filters.RangeFilter(
        field_name='heading',
        fields=(forms.FloatField(), forms.FloatField()),
        help_text='The heading of the sensor',
        label='Heading',
    )

    class Meta:
        model = Mesh3DSpatial
        fields = ['heading']
