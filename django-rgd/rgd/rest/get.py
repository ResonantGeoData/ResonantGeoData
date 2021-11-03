from rest_framework.generics import RetrieveAPIView
from rgd import models, serializers
from rgd.rest.mixins import BaseRestViewMixin


class GetSpatialAsset(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.SpatialAssetSerializer
    lookup_field = 'spatial_id'
    queryset = models.SpatialAsset.objects.all()
