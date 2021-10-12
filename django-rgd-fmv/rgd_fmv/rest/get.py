from rest_framework.generics import RetrieveAPIView
from rgd.mixins import BaseRestViewMixin
from rgd_fmv import models, serializers


class GetFMVMeta(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.FMVMetaSerializer
    lookup_field = 'pk'
    queryset = models.FMVMeta.objects.all()


class GetFMVDataEntry(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.FMVMetaDataSerializer
    lookup_field = 'pk'
    queryset = models.FMVMeta.objects.all()
