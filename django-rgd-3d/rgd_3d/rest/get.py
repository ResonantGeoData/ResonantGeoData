from rest_framework.generics import RetrieveAPIView
from rgd.rest.mixins import BaseRestViewMixin
from rgd_3d import models, serializers


class GetPointCloudMeta(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.PointCloudMetaSerializer
    lookup_field = 'pk'
    queryset = models.PointCloudMeta.objects.all()


class GetPointCloudMetaData(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.PointCloudMetaDataSerializer
    lookup_field = 'pk'
    queryset = models.PointCloudMeta.objects.all()
