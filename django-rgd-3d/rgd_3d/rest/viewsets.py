from rest_framework.decorators import action
from rgd.rest.base import ReadOnlyModelViewSet
from rgd_3d import models, serializers


class PointCloudMetaViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.PointCloudMetaSerializer
    queryset = models.PointCloudMeta.objects.all()

    @action(
        detail=True,
        serializer_class=serializers.PointCloudMetaDataSerializer,
    )
    def base64(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
