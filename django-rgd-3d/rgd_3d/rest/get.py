from rest_framework.generics import RetrieveAPIView
from rgd.rest.get import _PermissionMixin
from rgd_3d import models, serializers


class GetPointCloudMeta(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.PointCloudMetaSerializer
    lookup_field = 'pk'
    queryset = models.PointCloudMeta.objects.all()


class GetPointCloudMetaData(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.PointCloudMetaDataSerializer
    lookup_field = 'pk'
    queryset = models.PointCloudMeta.objects.all()
