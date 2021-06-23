from rest_framework.generics import RetrieveAPIView
from rgd.rest.get import _PermissionMixin
from rgd_imagery import models, serializers


class GetConvertedImageStatus(RetrieveAPIView, _PermissionMixin):
    """Get the status of a ConvertedImage by PK."""

    serializer_class = serializers.ConvertedImageSerializer
    lookup_field = 'pk'
    queryset = models.ConvertedImage.objects.all()


class GetSubsampledImage(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.SubsampledImageSerializer
    lookup_field = 'pk'
    queryset = models.SubsampledImage.objects.all()


class GetImageMeta(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ImageMetaSerializer
    lookup_field = 'pk'
    queryset = models.ImageMeta.objects.all()


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
