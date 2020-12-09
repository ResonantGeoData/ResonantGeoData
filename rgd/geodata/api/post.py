from rest_framework.generics import CreateAPIView

from .. import serializers
from ..models.imagery import ConvertedImageFile


class ConvertImageToCog(CreateAPIView):
    queryset = ConvertedImageFile.objects.all()
    serializer_class = serializers.ConvertedImageFileSerializer
