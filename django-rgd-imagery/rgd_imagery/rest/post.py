from rest_framework.generics import CreateAPIView
from rgd_imagery import models, serializers


class CreateConvertedImage(CreateAPIView):
    queryset = models.ConvertedImage.objects.all()
    serializer_class = serializers.ConvertedImageSerializer


class CreateSubsampledImage(CreateAPIView):
    queryset = models.SubsampledImage.objects.all()
    serializer_class = serializers.SubsampledImageSerializer


class CreateRasterSTAC(CreateAPIView):
    queryset = models.RasterMetaEntry.objects.all()
    serializer_class = serializers.STACRasterSerializer
