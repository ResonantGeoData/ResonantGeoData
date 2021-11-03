from rest_framework.generics import CreateAPIView
from rgd import models, serializers
from rgd.rest.mixins import BaseRestViewMixin


class CreateSpatialAsset(BaseRestViewMixin, CreateAPIView):
    queryset = models.SpatialAsset.objects.all()
    serializer_class = serializers.SpatialAssetSerializer
