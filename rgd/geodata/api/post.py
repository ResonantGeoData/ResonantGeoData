from rest_framework.generics import CreateAPIView

from ..models.imagery import ConvertedImageFile
from .. import serializers


class ConvertImageToCog(CreateAPIView):
    queryset = ConvertedImageFile.objects.all()
    serializer_class = serializers.ConvertedImageFileSerializer
