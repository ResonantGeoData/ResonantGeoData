from rest_framework.generics import ListAPIView
from rgd import serializers
from rgd.filters import SpatialEntryFilter
from rgd.models import SpatialEntry
from rgd.rest.mixins import BaseRestViewMixin


class SearchSpatialEntryView(BaseRestViewMixin, ListAPIView):
    queryset = SpatialEntry.objects.all()
    serializer_class = serializers.SpatialEntrySerializer
    filterset_class = SpatialEntryFilter
