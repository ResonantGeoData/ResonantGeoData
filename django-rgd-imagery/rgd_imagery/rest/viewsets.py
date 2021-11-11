from django.http import HttpResponseRedirect
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rgd.models.mixins import Status
from rgd.rest.base import ModelViewSet
from rgd.rest.mixins import TaskEventViewSetMixin
from rgd_imagery import models, serializers


class ProcessedImageViewSet(ModelViewSet):
    serializer_class = serializers.ProcessedImageSerializer
    queryset = models.ProcessedImage.objects.all()


class ProcessedImageGroupViewSet(ModelViewSet):
    serializer_class = serializers.ProcessedImageGroupSerializer
    queryset = models.ProcessedImageGroup.objects.all()

    # TODO: This should use a serializer instead.
    @swagger_auto_schema(
        method='GET',
        operation_summary='Get status counts of each ProcessedImage in the group.',
    )
    @action(detail=True)
    def status(self, *args, **kwargs):
        # TODO: This should use a more efficient aggregate.
        obj = self.get_object()
        images = models.ProcessedImage.objects.filter(group=obj)
        data = {
            Status.CREATED: images.filter(status=Status.CREATED).count(),
            Status.QUEUED: images.filter(status=Status.QUEUED).count(),
            Status.RUNNING: images.filter(status=Status.RUNNING).count(),
            Status.FAILED: images.filter(status=Status.FAILED).count(),
            Status.SUCCEEDED: images.filter(status=Status.SUCCEEDED).count(),
        }
        return Response(data)


class ImageSetViewSet(ModelViewSet):
    serializer_class = serializers.ImageSetSerializer
    queryset = models.ImageSet.objects.all()


class ImageSetSpatialViewSet(ModelViewSet):
    serializer_class = serializers.ImageSetSpatialSerializer
    queryset = models.ImageSetSpatial.objects.all()


class ImageViewSet(ModelViewSet):
    # TODO: consolidate 'ImageSerializer' and 'ImageMetaSerializer'

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return serializers.ImageMetaSerializer
        return serializers.ImageSerializer

    def get_queryset(self):
        if self.action in {'list', 'retrieve'}:
            return models.ImageMeta.objects.all()
        return models.Image.objects.all()

    @swagger_auto_schema(
        method='GET',
        operation_summary='Download the associated Image data for this Image directly from S3.',
    )
    @action(detail=True)
    def data(self, *args, **kwargs):
        obj = self.get_object()
        url = obj.file.get_url()
        return HttpResponseRedirect(url)


class RasterViewSet(ModelViewSet, TaskEventViewSetMixin):
    # TODO: consolidate 'RasterSerializer' and 'RasterMetaSerializer'

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return serializers.RasterMetaSerializer
        return serializers.RasterSerializer

    def get_queryset(self):
        if self.action in {'list', 'retrieve'}:
            return models.RasterMeta.objects.all()
        return models.Raster.objects.all()
