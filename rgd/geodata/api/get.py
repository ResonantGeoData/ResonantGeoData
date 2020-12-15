from rest_framework.generics import RetrieveAPIView

from .. import serializers
from ..models.common import ArbitraryFile, SpatialEntry
from ..models.imagery import ConvertedImageFile, SubsampledImage


class GetConvertedImageStatus(RetrieveAPIView):
    """Get the status of a ConvertedImageFile by PK."""

    serializer_class = serializers.ConvertedImageFileSerializer
    lookup_field = 'pk'
    queryset = ConvertedImageFile.objects.all()


class GetSubsampledImage(RetrieveAPIView):
    serializer_class = serializers.SubsampledImageSerializer
    lookup_field = 'pk'
    queryset = SubsampledImage.objects.all()


class GetArbitraryFile(RetrieveAPIView):
    serializer_class = serializers.ArbitraryFileSerializer
    lookup_field = 'pk'
    queryset = ArbitraryFile.objects.all()


class GetSpatialEntry(RetrieveAPIView):
    serializer_class = serializers.SpatialEntrySerializer
    lookup_field = 'pk'
    queryset = SpatialEntry.objects.all()
