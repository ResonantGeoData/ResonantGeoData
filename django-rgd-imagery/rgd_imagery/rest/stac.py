from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rgd.models import Collection
from rgd.permissions import filter_read_perm
from rgd_imagery import models, serializers


class _PermissionMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        return filter_read_perm(self.request.user, queryset)


class RootView(GenericAPIView, _PermissionMixin):
    """See all the Collections a user can see."""

    serializer_class = serializers.stac.STACRootSerializer
    queryset = Collection.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class FeatureCollectionView(GenericAPIView, _PermissionMixin):
    """See the Items in the Collection."""

    serializer_class = serializers.stac.STACRasterFeatureCollectionSerializer
    queryset = models.RasterMeta.objects.all()

    def get(self, request, *args, pk=None, **kwargs):
        queryset = self.get_queryset().filter(
            parent_raster__image_set__images__file__collection=collection
        )
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)
