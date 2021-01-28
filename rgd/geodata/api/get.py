from rest_framework.generics import RetrieveAPIView

from .. import serializers
from ..models.common import ChecksumFile, SpatialEntry
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


class GetChecksumFile(RetrieveAPIView):
    serializer_class = serializers.ChecksumFileSerializer
    lookup_field = 'pk'
    queryset = ChecksumFile.objects.all()


class GetSpatialEntry(RetrieveAPIView):
    serializer_class = serializers.SpatialEntrySerializer
    lookup_field = 'spatial_id'
    queryset = SpatialEntry.objects.all()
