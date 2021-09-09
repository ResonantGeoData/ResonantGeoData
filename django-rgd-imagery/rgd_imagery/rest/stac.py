from django_filters import rest_framework as filters
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rgd.models import Collection
from rgd.permissions import filter_read_perm
from rgd_imagery import models, serializers

from ..filters import STACSimpleFilter
from ..pagination import STACPagination


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
        queryset = self.get_queryset().filter(parent_raster__image_set__images__file__collection=pk)
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class SimpleSearchView(GenericAPIView, _PermissionMixin):
    """Search items."""

    serializer_class = serializers.stac.STACRasterFeatureCollectionSerializer
    queryset = models.RasterMeta.objects.all()
    pagination_class = STACPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = STACSimpleFilter

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)
