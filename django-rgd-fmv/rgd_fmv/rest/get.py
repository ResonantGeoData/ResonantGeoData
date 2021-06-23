from rest_framework.generics import RetrieveAPIView
from rgd.rest.get import _PermissionMixin
from rgd_fmv import models, serializers


class GetFMVMeta(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.FMVMetaSerializer
    lookup_field = 'pk'
    queryset = models.FMVMeta.objects.all()


class GetFMVDataEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.FMVMetaDataSerializer
    lookup_field = 'pk'
    queryset = models.FMVMeta.objects.all()
