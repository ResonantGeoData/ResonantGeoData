from rest_framework.generics import ListAPIView
from rgd import serializers
from rgd.filters import SpatialEntryFilter
from rgd.mixins import BaseRestViewMixin
from rgd.models import SpatialEntry


class SearchSpatialEntryView(BaseRestViewMixin, ListAPIView):
    queryset = SpatialEntry.objects.all()
    serializer_class = serializers.SpatialEntrySerializer
    filterset_class = SpatialEntryFilter
