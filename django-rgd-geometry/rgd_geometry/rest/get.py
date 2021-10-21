from rest_framework.generics import RetrieveAPIView
from rgd.rest.mixins import BaseRestViewMixin
from rgd_geometry import models, serializers


class GetGeometry(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.GeometrySerializer
    lookup_field = 'pk'
    queryset = models.Geometry.objects.all()


class GetGeometryData(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.GeometryDataSerializer
    lookup_field = 'pk'
    queryset = models.Geometry.objects.all()
