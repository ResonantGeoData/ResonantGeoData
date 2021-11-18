from rest_framework.decorators import action
from rgd.rest.base import ReadOnlyModelViewSet
from rgd_geometry import models, serializers


class GeometryViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.GeometrySerializer
    queryset = models.Geometry.objects.all()

    @action(
        detail=True,
        serializer_class=serializers.GeometryDataSerializer,
    )
    def data(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
