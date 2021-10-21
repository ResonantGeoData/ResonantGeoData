from rest_framework.generics import CreateAPIView
from rgd import models, serializers
from rgd.rest.mixins import BaseRestViewMixin


class CreateCollection(BaseRestViewMixin, CreateAPIView):
    queryset = models.Collection.objects.all()
    serializer_class = serializers.CollectionSerializer


class CreateCollectionPermission(BaseRestViewMixin, CreateAPIView):
    queryset = models.CollectionPermission.objects.all()
    serializer_class = serializers.CollectionPermissionSerializer


class CreateChecksumFile(BaseRestViewMixin, CreateAPIView):
    queryset = models.ChecksumFile.objects.all()
    serializer_class = serializers.ChecksumFileSerializer


class CreateSpatialAsset(BaseRestViewMixin, CreateAPIView):
    queryset = models.SpatialAsset.objects.all()
    serializer_class = serializers.SpatialAssetSerializer
