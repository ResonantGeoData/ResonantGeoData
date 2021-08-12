from rest_framework.generics import RetrieveAPIView
from rgd.rest.get import _PermissionMixin
from rgd_imagery import models, serializers


class GetProcessedImage(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ProcessedImageSerializer
    lookup_field = 'pk'
    queryset = models.ProcessedImage.objects.all()


class GetImageMeta(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ImageMetaSerializer
    lookup_field = 'pk'
    queryset = models.ImageMeta.objects.all()


class GetImageSet(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ImageSetSerializer
    lookup_field = 'pk'
    queryset = models.ImageSet.objects.all()


class GetRasterMeta(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.RasterMetaSerializer
    lookup_field = 'pk'
    queryset = models.RasterMeta.objects.all()


class GetRasterMetaSTAC(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.STACRasterSerializer
    lookup_field = 'pk'
    queryset = models.RasterMeta.objects.all()
