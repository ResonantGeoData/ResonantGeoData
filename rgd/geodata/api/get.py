from rest_framework.generics import RetrieveAPIView

from rgd.geodata.permissions import check_read_perm

from .. import serializers
from ..models.common import ChecksumFile, SpatialEntry
from ..models.imagery import ConvertedImageFile, SubsampledImage


class _PermissionMixin:
    def get_object(self):
        obj = super().get_object()
        check_read_perm(obj)
        return obj


class GetConvertedImageStatus(RetrieveAPIView, _PermissionMixin):
    """Get the status of a ConvertedImageFile by PK."""

    serializer_class = serializers.ConvertedImageFileSerializer
    lookup_field = 'pk'
    queryset = ConvertedImageFile.objects.all()


class GetSubsampledImage(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.SubsampledImageSerializer
    lookup_field = 'pk'
    queryset = SubsampledImage.objects.all()


class GetChecksumFile(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ChecksumFileSerializer
    lookup_field = 'pk'
    queryset = ChecksumFile.objects.all()


class GetSpatialEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.SpatialEntrySerializer
    lookup_field = 'spatial_id'
    queryset = SpatialEntry.objects.all()
