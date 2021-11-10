from rest_framework.generics import RetrieveAPIView
from rgd.rest.mixins import BaseRestViewMixin
from rgd_imagery import models, serializers


class GetRasterMetaSTAC(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.stac.ItemSerializer
    lookup_field = 'pk'
    queryset = models.RasterMeta.objects.all()
