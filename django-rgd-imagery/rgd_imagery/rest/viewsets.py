from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rgd.models.mixins import Status
from rgd.rest.base import ModelViewSet
from rgd.rest.mixins import TaskEventViewSetMixin
from rgd.utility import get_file_data_url
from rgd_imagery import filters, models, serializers, stac


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


class ImageViewSet(ModelViewSet, TaskEventViewSetMixin):
    # TODO: consolidate 'ImageSerializer' and 'ImageMetaSerializer'

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve', 'status'}:
            return serializers.ImageMetaSerializer
        return serializers.ImageSerializer

    def get_queryset(self):
        if self.action in {'list', 'retrieve', 'status'}:
            return models.ImageMeta.objects.all()
        return models.Image.objects.all()

    @swagger_auto_schema(
        method='GET',
        operation_summary='Download the associated Image data for this Image directly from S3.',
    )
    @action(detail=True)
    def data(self, *args, **kwargs):
        obj: models.Image = self.get_object()
        return get_file_data_url(obj.file)


class RasterMetaViewSet(ModelViewSet):
    filterset_class = filters.RasterMetaFilter

    def get_serializer_class(self):
        if self.action in {'update', 'partial_update', 'destroy', 'create', 'status'}:
            return serializers.RasterSerializer
        return serializers.RasterMetaSerializer

    def get_queryset(self):
        if self.action in {'update', 'partial_update', 'destroy', 'create', 'status'}:
            self.filterset_class = None
            return models.Raster.objects.all()
        return models.RasterMeta.objects.all()

    @swagger_auto_schema(
        method='GET',
        operation_summary='Fetch the STAC Item JSON for this raster.',
    )
    @action(detail=True)
    def stac(self, request, *args, pk=None, **kwargs):
        queryset = stac.querysets.item.get_queryset(pk=pk)
        data = stac.serializers.item.get_item(queryset.get(), request)
        return Response(data)

    @swagger_auto_schema(
        method='GET',
        operation_summary='Check the status.',
    )
    @action(detail=True)
    def status(self, *args, **kwargs):
        return self.retrieve(self, *args, **kwargs)
