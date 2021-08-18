from rest_framework.generics import CreateAPIView
from rgd import models, serializers


class CreateCollection(CreateAPIView):
    queryset = models.Collection.objects.all()
    serializer_class = serializers.CollectionSerializer


class CreateCollectionPermission(CreateAPIView):
    queryset = models.CollectionPermission.objects.all()
    serializer_class = serializers.CollectionPermissionSerializer


class CreateChecksumFile(CreateAPIView):
    queryset = models.ChecksumFile.objects.all()
    serializer_class = serializers.ChecksumFileSerializer


class CreateSpatialAsset(CreateAPIView):
    queryset = models.SpatialAsset.objects.all()
    serializer_class = serializers.SpatialAssetSerializer
