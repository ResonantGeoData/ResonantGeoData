from rest_framework.decorators import action
from rgd.rest.base import ModelViewSet
from rgd_fmv import models, serializers


class FMVViewSet(ModelViewSet):
    queryset = models.FMVMeta.objects.all()

    def get_serializer_class(self):
        if self.action in ['get', 'list']:
            return serializers.FMVMetaSerializer
        return serializers.FMVSerializer

    @action(detail=True, serializer_class=serializers.FMVMetaDataSerializer)
    def data(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
