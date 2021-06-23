from rest_framework.generics import RetrieveAPIView
from rgd.rest.get import _PermissionMixin
from rgd_geometry import models, serializers


class GetGeometry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.GeometrySerializer
    lookup_field = 'pk'
    queryset = models.Geometry.objects.all()


class GetGeometryData(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.GeometryDataSerializer
    lookup_field = 'pk'
    queryset = models.Geometry.objects.all()
