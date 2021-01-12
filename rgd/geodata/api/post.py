from rest_framework.generics import CreateAPIView

from .. import serializers
from ..models.imagery import ConvertedImageFile, SubsampledImage


class CreateConvertedImageFile(CreateAPIView):
    queryset = ConvertedImageFile.objects.all()
    serializer_class = serializers.ConvertedImageFileSerializer


class CreateSubsampledImage(CreateAPIView):
    queryset = SubsampledImage.objects.all()
    serializer_class = serializers.SubsampledImageSerializer
