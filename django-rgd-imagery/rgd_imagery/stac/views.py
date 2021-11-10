from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rgd.models import Collection
from rgd.rest.mixins import BaseRestViewMixin
from rgd_imagery import models, serializers

from ..filters import STACSimpleFilter
from ..pagination import STACPagination


class CoreView(BaseRestViewMixin, GenericAPIView):
    """See all the Collections a user can see."""

    serializer_class = serializers.stac.CoreSerializer
    queryset = Collection.objects.all()

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class CollectionView(BaseRestViewMixin, GenericAPIView):
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


class ItemCollectionView(BaseRestViewMixin, GenericAPIView):
    """See the Items in the Collection."""

    serializer_class = serializers.stac.ItemCollectionSerializer
    queryset = models.RasterMeta.objects.all()

    def get(self, request, *args, collection_id=None, **kwargs):
        collection_id = None if collection_id == 'default' else collection_id
        queryset = self.get_queryset().filter(
            parent_raster__image_set__images__file__collection=collection_id
        )
        # Test if queryset is too large
        stac_browser_limit = getattr(settings, 'RGD_STAC_BROWSER_LIMIT', 1000)
        num_items = queryset.count()
        if num_items > stac_browser_limit:
            raise ValueError(
                f"'RGD_STAC_BROWSER_LIMIT' ({stac_browser_limit}) exceeded. "
                f'Requested collection with {num_items} items.'
            )
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class SimpleSearchView(BaseRestViewMixin, GenericAPIView):
    """Search items."""

    serializer_class = serializers.stac.ItemCollectionSerializer
    queryset = models.RasterMeta.objects.all()
    pagination_class = STACPagination
    filterset_class = STACSimpleFilter

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset)
        return Response(serializer.data)


class ItemView(BaseRestViewMixin, GenericAPIView):
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
