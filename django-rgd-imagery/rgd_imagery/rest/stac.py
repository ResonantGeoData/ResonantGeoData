from django_filters import rest_framework as filters
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rgd.models import Collection
from rgd.permissions import filter_read_perm
from rgd_imagery import models, serializers

from ..filters import STACSimpleFilter
from ..pagination import STACPagination


class BaseSTACView(GenericAPIView):
    def get_queryset(self):
        """Filter the queryset to items visible by the requester."""
        queryset = super().get_queryset()
        return filter_read_perm(self.request.user, queryset)


class CoreView(BaseSTACView):
    """See all the Collections a user can see."""

    serializer_class = serializers.stac.CoreSerializer
    queryset = Collection.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class CollectionView(BaseSTACView):
    """Metadata regarding a collection."""

    serializer_class = serializers.stac.CollectionSerializer
    queryset = Collection.objects.all()

    def get(self, request, *args, collection_id=None, **kwargs):
        queryset = self.get_queryset()
        if collection_id != 'default':
            collection = queryset.get(pk=collection_id)
        else:
            collection = Collection()
        serializer = self.get_serializer(collection)
        return Response(serializer.data)


class ItemCollectionView(BaseSTACView):
    """See the Items in the Collection."""

    serializer_class = serializers.stac.ItemCollectionSerializer
    queryset = models.RasterMeta.objects.all()

    def get(self, request, *args, collection_id=None, **kwargs):
        collection_id = None if collection_id == 'default' else collection_id
        queryset = self.get_queryset().filter(
            parent_raster__image_set__images__file__collection=collection_id
        )
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class SimpleSearchView(BaseSTACView):
    """Search items."""

    serializer_class = serializers.stac.ItemCollectionSerializer
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


class ItemView(BaseSTACView):
    """See the Items in the Collection."""

    serializer_class = serializers.stac.ItemSerializer
    queryset = models.RasterMeta.objects.all()

    def get(self, request, *args, collection_id=None, item_id=None, **kwargs):
        collection_id = None if collection_id == 'default' else collection_id
        queryset = self.get_queryset().filter(
            parent_raster__image_set__images__file__collection=collection_id
        )
        item = queryset.get(pk=item_id)
        serializer = self.get_serializer(item)
        return Response(serializer.data)
