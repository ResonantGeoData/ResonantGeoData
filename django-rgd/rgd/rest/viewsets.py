from django.http import HttpResponseRedirect
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rgd import models, serializers
from rgd.filters import SpatialEntryFilter
from rgd.rest.base import ModelViewSet, ReadOnlyModelViewSet


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


class SpatialEntryViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.SpatialEntrySerializer
    queryset = models.SpatialEntry.objects.all()
    filterset_class = SpatialEntryFilter

    @swagger_auto_schema(
        method='GET',
        operation_summary='Get the footprint of this SpatialEntry.',
    )
    @action(detail=True, serializer_class=serializers.SpatialEntryFootprintSerializer)
    def footprint(self, request, pk=None):
        return self.retrieve(request, pk=pk)


class SpatialAssetViewSet(ModelViewSet):
    serializer_class = serializers.SpatialAssetSerializer
    queryset = models.SpatialAsset.objects.all()
