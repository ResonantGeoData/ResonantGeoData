from django.http import HttpResponseRedirect
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rgd import models, serializers
from rgd.rest.base import ModelViewSet


class CollectionViewSet(ModelViewSet):
    serializer_class = serializers.CollectionSerializer
    queryset = models.Collection.objects.all()


class CollectionPermissionViewSet(ModelViewSet):
    serializer_class = serializers.CollectionPermissionSerializer
    queryset = models.CollectionPermission.objects.all()


class ChecksumFileViewSet(ModelViewSet):
    serializer_class = serializers.ChecksumFileSerializer
    queryset = models.ChecksumFile.objects.all()

    @swagger_auto_schema(
        method='GET',
        operation_summary='Download ChecksumFile data directly from S3.',
    )
    @action(detail=True)
    def data(self, request, pk=None):
        obj = self.get_object()
        return HttpResponseRedirect(obj.get_url())
