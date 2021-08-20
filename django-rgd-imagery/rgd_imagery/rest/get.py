from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rgd.models.mixins import Status
from rgd.permissions import check_read_perm
from rgd.rest.get import _PermissionMixin
from rgd_imagery import models, serializers


class GetProcessedImage(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ProcessedImageSerializer
    lookup_field = 'pk'
    queryset = models.ProcessedImage.objects.all()


class GetImageMeta(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ImageMetaSerializer
    lookup_field = 'pk'
    queryset = models.ImageMeta.objects.all()


class GetImageSet(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ImageSetSerializer
    lookup_field = 'pk'
    queryset = models.ImageSet.objects.all()


class GetImageSetSpatial(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.ImageSetSpatialSerializer
    lookup_field = 'pk'
    queryset = models.ImageSetSpatial.objects.all()


class GetRasterMeta(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.RasterMetaSerializer
    lookup_field = 'pk'
    queryset = models.RasterMeta.objects.all()


class GetRasterMetaSTAC(RetrieveAPIView, _PermissionMixin):
    serializer_class = serializers.STACRasterSerializer
    lookup_field = 'pk'
    queryset = models.RasterMeta.objects.all()


@swagger_auto_schema(
    method='GET',
    operation_summary='Get status counts of each ProcessedImage in the group.',
)
@api_view(['GET'])
def get_processed_image_group_status(request, pk):
    instance = get_object_or_404(models.ProcessedImageGroup, pk=pk)
    check_read_perm(request.user, instance)
    images = models.ProcessedImage.objects.filter(group=instance)
    data = {
        Status.CREATED: images.filter(status=Status.CREATED).count(),
        Status.QUEUED: images.filter(status=Status.QUEUED).count(),
        Status.RUNNING: images.filter(status=Status.RUNNING).count(),
        Status.FAILED: images.filter(status=Status.FAILED).count(),
        Status.SUCCEEDED: images.filter(status=Status.SUCCEEDED).count(),
    }
    return Response(data)
