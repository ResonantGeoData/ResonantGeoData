from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.response import Response
from rgd.models.mixins import Status
from rgd.rest.base import ModelViewSet
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
