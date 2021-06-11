from rest_framework.generics import RetrieveAPIView

from rgd.rest.get import _PermissionMixin

from rgd_3d import models, serializers


class GetPointCloudEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.PointCloudEntrySerializer
    lookup_field = 'pk'
    queryset = models.PointCloudEntry.objects.all()


class GetPointCloudEntryData(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.PointCloudEntryDataSerializer
    lookup_field = 'pk'
    queryset = models.PointCloudEntry.objects.all()
