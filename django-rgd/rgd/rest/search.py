from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rgd import serializers
from rgd.filters import SpatialEntryFilter
from rgd.models import SpatialEntry
from rgd.permissions import filter_read_perm


class SearchSpatialEntryView(ListAPIView):
    queryset = SpatialEntry.objects.all()
    serializer_class = serializers.SpatialEntrySerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = SpatialEntryFilter

    def get_queryset(self):
        return filter_read_perm(self.request.user, super().get_queryset())
