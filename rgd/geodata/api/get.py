from rest_framework.generics import RetrieveAPIView

from .. import serializers
from ..models.imagery import ConvertedImageFile


class GetConvertedImageStatus(RetrieveAPIView):
    """Get the status of a ConvertedImageFile by PK."""

    serializer_class = serializers.ConvertedImageFileSerializer
    lookup_field = 'pk'
    queryset = ConvertedImageFile.objects.all()
