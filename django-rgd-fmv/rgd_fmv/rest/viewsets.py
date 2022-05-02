from rest_framework.decorators import action
from rgd.rest.base import ModelViewSet, ReadOnlyModelViewSet
from rgd_fmv import models, serializers


class FMVMetaViewSet(ReadOnlyModelViewSet):
    queryset = models.FMVMeta.objects.all()
    serializer_class = serializers.FMVMetaSerializer

    @action(detail=True, serializer_class=serializers.FMVMetaDataSerializer)
    def data(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class FMVViewSet(ModelViewSet):
    queryset = models.FMV.objects.all()
    serializer_class = serializers.FMVSerializer
