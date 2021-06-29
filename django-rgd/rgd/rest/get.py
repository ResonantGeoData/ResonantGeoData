from rest_framework.generics import RetrieveAPIView
from rgd import models, serializers
from rgd.permissions import check_read_perm


class _PermissionMixin:
    def get_object(self):
        obj = super().get_object()
        check_read_perm(self.request.user, obj)
        return obj


class GetChecksumFile(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ChecksumFileSerializer
    lookup_field = 'pk'
    queryset = models.ChecksumFile.objects.all()


class GetSpatialEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.SpatialEntrySerializer
    lookup_field = 'spatial_id'
    queryset = models.SpatialEntry.objects.all()


class GetSpatialEntryFootprint(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.SpatialEntryFootprintSerializer
    lookup_field = 'spatial_id'
    queryset = models.SpatialEntry.objects.all()
