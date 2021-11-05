from rest_framework.decorators import action
from rgd.rest.base import ReadOnlyModelViewSet
from rgd_fmv import models, serializers


class FMVMetaViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.FMVMetaSerializer
    queryset = models.FMVMeta.objects.all()

    @action(detail=True, serializer_class=serializers.FMVMetaDataSerializer)
    def data(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
