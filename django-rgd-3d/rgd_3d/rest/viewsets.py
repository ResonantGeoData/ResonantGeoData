from rest_framework.decorators import action
from rgd.rest.base import ReadOnlyModelViewSet
from rgd.rest.mixins import TaskEventViewSetMixin
from rgd_3d import models, serializers


class Mesh3DMetaViewSet(ReadOnlyModelViewSet, TaskEventViewSetMixin):
    serializer_class = serializers.Mesh3DMetaSerializer
    queryset = models.Mesh3DMeta.objects.all()

    @action(
        detail=True,
        serializer_class=serializers.Mesh3DMetaDataSerializer,
    )
    def base64(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
