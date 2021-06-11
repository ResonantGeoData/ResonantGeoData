from rest_framework.generics import RetrieveAPIView
from rgd.rest.get import _PermissionMixin
from rgd_geometry import models, serializers


class GetGeometryEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.GeometryEntrySerializer
    lookup_field = 'pk'
    queryset = models.GeometryEntry.objects.all()


class GetGeometryEntryData(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.GeometryEntryDataSerializer
    lookup_field = 'pk'
    queryset = models.GeometryEntry.objects.all()
