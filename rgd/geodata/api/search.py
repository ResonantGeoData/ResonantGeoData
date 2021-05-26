from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView

from rgd.geodata import serializers
from rgd.geodata.filters import RasterMetaEntryFilter, SpatialEntryFilter
from rgd.geodata.models import RasterMetaEntry, SpatialEntry
from rgd.geodata.permissions import filter_read_perm


class SearchSpatialEntryView(ListAPIView):
    queryset = SpatialEntry.objects.all()
    serializer_class = serializers.SpatialEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SpatialEntryFilter

    def get_queryset(self):
        return filter_read_perm(self.request.user, super().get_queryset())


class SearchRasterMetaEntrySTACView(ListAPIView):
    queryset = RasterMetaEntry.objects.all()
    serializer_class = serializers.STACRasterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RasterMetaEntryFilter

    def get_queryset(self):
        return filter_read_perm(self.request.user, super().get_queryset())
