from rest_framework.generics import RetrieveAPIView
from rgd.rest.get import _PermissionMixin
from rgd_fmv import models, serializers


class GetFMVEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.FMVEntrySerializer
    lookup_field = 'pk'
    queryset = models.FMVEntry.objects.all()


class GetFMVDataEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.FMVEntryDataSerializer
    lookup_field = 'pk'
    queryset = models.FMVEntry.objects.all()
