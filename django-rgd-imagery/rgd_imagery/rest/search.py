from rest_framework.generics import ListAPIView
from rgd.rest.mixins import BaseRestViewMixin
from rgd_imagery import serializers
from rgd_imagery.filters import RasterMetaFilter
from rgd_imagery.models import RasterMeta


class SearchRasterMetaSTACView(BaseRestViewMixin, ListAPIView):
    queryset = RasterMeta.objects.all()
    serializer_class = serializers.stac.ItemSerializer
    filterset_class = RasterMetaFilter
