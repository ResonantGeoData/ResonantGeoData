from rest_framework.generics import CreateAPIView

from .. import serializers
from .. import models


class CreateConvertedImageFile(CreateAPIView):
    queryset = models.ConvertedImageFile.objects.all()
    serializer_class = serializers.ConvertedImageFileSerializer


class CreateSubsampledImage(CreateAPIView):
    queryset = models.SubsampledImage.objects.all()
    serializer_class = serializers.SubsampledImageSerializer


class CreateRasterSTAC(CreateAPIView):
    queryset = models.RasterMetaEntry.objects.all()
    serializer_class = serializers.STACRasterSerializer
