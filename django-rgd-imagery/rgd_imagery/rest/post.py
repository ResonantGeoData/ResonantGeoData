from rest_framework.generics import CreateAPIView
from rgd_imagery import models, serializers


class CreateConvertedImageFile(CreateAPIView):
    queryset = models.ConvertedImageFile.objects.all()
    serializer_class = serializers.ConvertedImageFileSerializer


class CreateSubsampledImage(CreateAPIView):
    queryset = models.SubsampledImage.objects.all()
    serializer_class = serializers.SubsampledImageSerializer


class CreateRasterSTAC(CreateAPIView):
    queryset = models.RasterMetaEntry.objects.all()
    serializer_class = serializers.STACRasterSerializer
