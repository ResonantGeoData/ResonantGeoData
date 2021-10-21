from rest_framework.generics import RetrieveAPIView
from rgd import models, serializers
from rgd.rest.mixins import BaseRestViewMixin


class GetCollection(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.CollectionSerializer
    lookup_field = 'pk'
    queryset = models.Collection.objects.all()


class GetCollectionPermission(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.CollectionPermissionSerializer
    lookup_field = 'pk'
    queryset = models.CollectionPermission.objects.all()


class GetChecksumFile(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.ChecksumFileSerializer
    lookup_field = 'pk'
    queryset = models.ChecksumFile.objects.all()


class GetSpatialEntry(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.SpatialEntrySerializer
    lookup_field = 'spatial_id'
    queryset = models.SpatialEntry.objects.all()


class GetSpatialEntryFootprint(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.SpatialEntryFootprintSerializer
    lookup_field = 'spatial_id'
    queryset = models.SpatialEntry.objects.all()


class GetSpatialAsset(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.SpatialAssetSerializer
    lookup_field = 'spatial_id'
    queryset = models.SpatialAsset.objects.all()
