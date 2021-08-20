from rest_framework.generics import CreateAPIView
from rgd_imagery import models, serializers


class CreateProcessedImage(CreateAPIView):
    queryset = models.ProcessedImage.objects.all()
    serializer_class = serializers.ProcessedImageSerializer


class CreateProcessedImageGroup(CreateAPIView):
    queryset = models.ProcessedImageGroup.objects.all()
    serializer_class = serializers.ProcessedImageGroupSerializer


class CreateRasterSTAC(CreateAPIView):
    queryset = models.RasterMeta.objects.all()
    serializer_class = serializers.STACRasterSerializer


class CreateImage(CreateAPIView):
    queryset = models.Image.objects.all()
    serializer_class = serializers.ImageSerializer


class CreateImageSet(CreateAPIView):
    queryset = models.ImageSet.objects.all()
    serializer_class = serializers.ImageSetSerializer


class CreateImageSetSpatial(CreateAPIView):
    queryset = models.ImageSetSpatial.objects.all()
    serializer_class = serializers.ImageSetSpatialSerializer


class CreateRaster(CreateAPIView):
    queryset = models.Raster.objects.all()
    serializer_class = serializers.RasterSerializer
