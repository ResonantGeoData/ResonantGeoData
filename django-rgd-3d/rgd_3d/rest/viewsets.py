from rest_framework.decorators import action
from rgd.rest.base import ModelViewSet
from rgd.rest.mixins import TaskEventViewSetMixin
from rgd_3d import models, serializers


class Mesh3DViewSet(ModelViewSet, TaskEventViewSetMixin):
    serializer_class = serializers.Mesh3DSerializer
    queryset = models.Mesh3D.objects.all()

    @action(
        detail=True,
        serializer_class=serializers.Mesh3DDataSerializer,
    )
    def base64(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
