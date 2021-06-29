from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.generics import ListAPIView
from rgd.permissions import filter_read_perm
from rgd_imagery import serializers
from rgd_imagery.filters import RasterMetaFilter
from rgd_imagery.models import RasterMeta


class SearchRasterMetaSTACView(ListAPIView):
    queryset = RasterMeta.objects.all()
    serializer_class = serializers.STACRasterSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RasterMetaFilter

    def get_queryset(self):
        return filter_read_perm(self.request.user, super().get_queryset())
