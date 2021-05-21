from rest_framework.generics import RetrieveAPIView

from rgd.geodata.permissions import check_read_perm

from .. import models, serializers


class _PermissionMixin:
    def get_object(self):
        obj = super().get_object()
        check_read_perm(self.request.user, obj)
        return obj


class GetConvertedImageStatus(RetrieveAPIView, _PermissionMixin):
    """Get the status of a ConvertedImageFile by PK."""

    serializer_class = serializers.ConvertedImageFileSerializer
    lookup_field = 'pk'
    queryset = models.ConvertedImageFile.objects.all()


class GetSubsampledImage(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.SubsampledImageSerializer
    lookup_field = 'pk'
    queryset = models.SubsampledImage.objects.all()


class GetChecksumFile(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ChecksumFileSerializer
    lookup_field = 'pk'
    queryset = models.ChecksumFile.objects.all()


class GetSpatialEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.SpatialEntrySerializer
    lookup_field = 'spatial_id'
    queryset = models.SpatialEntry.objects.all()


class GetImageEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ImageEntrySerializer
    lookup_field = 'pk'
    queryset = models.ImageEntry.objects.all()


class GetImageSet(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ImageSetSerializer
    lookup_field = 'pk'
    queryset = models.ImageSet.objects.all()


class GetRasterMetaEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.RasterMetaEntrySerializer
    lookup_field = 'pk'
    queryset = models.RasterMetaEntry.objects.all()


class GetRasterMetaEntrySTAC(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.STACRasterSerializer
    lookup_field = 'pk'
    queryset = models.RasterMetaEntry.objects.all()


class GetGeometryEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.GeometryEntrySerializer
    lookup_field = 'pk'
    queryset = models.GeometryEntry.objects.all()


class GetGeometryEntryData(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.GeometryEntryDataSerializer
    lookup_field = 'pk'
    queryset = models.GeometryEntry.objects.all()


class GetFMVEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.FMVEntrySerializer
    lookup_field = 'pk'
    queryset = models.FMVEntry.objects.all()


class GetFMVDataEntry(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.FMVEntryDataSerializer
    lookup_field = 'pk'
    queryset = models.FMVEntry.objects.all()


class GetPointCloudEntry(
    RetrieveAPIView,
):  # _PermissionMixin):
    serializer_class = serializers.PointCloudEntrySerializer
    lookup_field = 'pk'
    queryset = models.PointCloudEntry.objects.all()


class GetPointCloudEntryData(RetrieveAPIView):
    serializer_class = serializers.PointCloudEntryDataSerializer
    lookup_field = 'pk'
    queryset = models.PointCloudEntry.objects.all()
