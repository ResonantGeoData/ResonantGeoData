from rest_framework.generics import CreateAPIView
from rgd_imagery import models, serializers


class CreateConvertedImage(CreateAPIView):
    queryset = models.ConvertedImage.objects.all()
    serializer_class = serializers.ConvertedImageSerializer


class CreateRegionImage(CreateAPIView):
    queryset = models.RegionImage.objects.all()
    serializer_class = serializers.RegionImageSerializer


class CreateRasterSTAC(CreateAPIView):
    queryset = models.RasterMeta.objects.all()
    serializer_class = serializers.STACRasterSerializer
