from rest_framework.generics import CreateAPIView
from rgd.rest.mixins import BaseRestViewMixin
from rgd_imagery import models, serializers


class CreateProcessedImage(BaseRestViewMixin, CreateAPIView):
    queryset = models.ProcessedImage.objects.all()
    serializer_class = serializers.ProcessedImageSerializer


class CreateProcessedImageGroup(BaseRestViewMixin, CreateAPIView):
    queryset = models.ProcessedImageGroup.objects.all()
    serializer_class = serializers.ProcessedImageGroupSerializer


class CreateRasterSTAC(BaseRestViewMixin, CreateAPIView):
    queryset = models.RasterMeta.objects.all()
    serializer_class = serializers.stac.ItemSerializer


class CreateImage(BaseRestViewMixin, CreateAPIView):
    queryset = models.Image.objects.all()
    serializer_class = serializers.ImageSerializer


class CreateImageSet(BaseRestViewMixin, CreateAPIView):
    queryset = models.ImageSet.objects.all()
    serializer_class = serializers.ImageSetSerializer


class CreateImageSetSpatial(BaseRestViewMixin, CreateAPIView):
    queryset = models.ImageSetSpatial.objects.all()
    serializer_class = serializers.ImageSetSpatialSerializer


class CreateRaster(BaseRestViewMixin, CreateAPIView):
    queryset = models.Raster.objects.all()
    serializer_class = serializers.RasterSerializer
