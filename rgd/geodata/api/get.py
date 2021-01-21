from django.http import JsonResponse
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveAPIView

from .. import models, serializers


class GetConvertedImageStatus(RetrieveAPIView):
    """Get the status of a ConvertedImageFile by PK."""

    serializer_class = serializers.ConvertedImageFileSerializer
    lookup_field = 'pk'
    queryset = models.ConvertedImageFile.objects.all()


class GetSubsampledImage(RetrieveAPIView):
    serializer_class = serializers.SubsampledImageSerializer
    lookup_field = 'pk'
    queryset = models.SubsampledImage.objects.all()


class GetArbitraryFile(RetrieveAPIView):
    serializer_class = serializers.ArbitraryFileSerializer
    lookup_field = 'pk'
    queryset = models.ArbitraryFile.objects.all()


class GetSpatialEntry(RetrieveAPIView):
    serializer_class = serializers.SpatialEntrySerializer
    lookup_field = 'spatial_id'
    queryset = models.SpatialEntry.objects.all()


class GetKWCOCOArchive(RetrieveAPIView):
    serializer_class = serializers.KWCOCOArchiveSerializer
    lookup_field = 'pk'
    queryset = models.KWCOCOArchive.objects.all()


class GetImageEntry(RetrieveAPIView):
    serializer_class = serializers.ImageEntrySerializer
    lookup_field = 'pk'
    queryset = models.ImageEntry.objects.all()


class GetAnnotation(RetrieveAPIView):
    serializer_class = serializers.AnnotationSerializer
    lookup_field = 'pk'
    queryset = models.Annotation.objects.all()
