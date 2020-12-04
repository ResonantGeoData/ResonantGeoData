from rest_framework.generics import RetrieveAPIView

from ..models.imagery import ConvertedImageFile
from .. import serializers


class GetConvertedImageStatus(RetrieveAPIView):
    """Get the status of a ConvertedImageFile by PK."""
    serializer_class = serializers.ConvertedImageFileSerializer
    lookup_field = 'pk'
    queryset = ConvertedImageFile.objects.all()
