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
