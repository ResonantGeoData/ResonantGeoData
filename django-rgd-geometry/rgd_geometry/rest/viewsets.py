from rest_framework.decorators import action
from rgd.rest.base import ModelViewSet
from rgd_geometry import models, serializers


class GeometryViewSet(ModelViewSet):
    serializer_class = serializers.GeometrySerializer
    queryset = models.Geometry.objects.all()

    @action(
        detail=True,
        serializer_class=serializers.GeometryDataSerializer,
    )
    def data(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class GeometryArchiveViewSet(ModelViewSet):
    serializer_class = serializers.GeometryArchiveSerializer
    queryset = models.GeometryArchive.objects.all()
