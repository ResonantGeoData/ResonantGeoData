from rest_framework.generics import CreateAPIView
from rgd.rest.mixins import BaseRestViewMixin
from rgd_imagery import models, serializers


class CreateRasterSTAC(BaseRestViewMixin, CreateAPIView):
    queryset = models.RasterMeta.objects.all()
    serializer_class = serializers.stac.ItemSerializer
