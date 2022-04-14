from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework import response, views
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rgd import models, serializers
from rgd.filters import CollectionFilter, SpatialEntryFilter
from rgd.models.file import ChecksumFile
from rgd.rest.base import ModelViewSet, ReadOnlyModelViewSet
from rgd.utility import get_file_data_url

from ..models import utils
from .authentication import UserSigner
from .mixins import BaseRestViewMixin, TaskEventViewSetMixin


class CollectionViewSet(ModelViewSet):
    serializer_class = serializers.CollectionSerializer
    queryset = models.Collection.objects.all()
    filterset_class = CollectionFilter

    @swagger_auto_schema(
        method='GET',
        operation_summary='Get the file at the given index in this collection. Associated files are ordered by primary key and the provided index is the index in that ordered set. If the files in the collection change, this will not be reproducible.',
    )
    @action(
        detail=True,
        serializer_class=serializers.ChecksumFileSerializer,
        url_path=r'item/(?P<index>\d+)',
    )
    def item(self, request, pk, index):
        collection = get_object_or_404(models.Collection, pk=pk)
        files = collection.checksumfiles.order_by('pk')
        try:
            instance = files[int(index)]
        except (IndexError, ValueError):
            raise ValidationError(f'index {index} not valid or out of range.')
        return Response(serializers.ChecksumFileSerializer(instance).data)


class CollectionPermissionViewSet(ModelViewSet):
    serializer_class = serializers.CollectionPermissionSerializer
    queryset = models.CollectionPermission.objects.all()


class ChecksumFileViewSet(ModelViewSet, TaskEventViewSetMixin):
    serializer_class = serializers.ChecksumFileSerializer
    queryset = models.ChecksumFile.objects.all()

    @swagger_auto_schema(query_serializer=serializers.ChecksumFileListQuerySerializer())
    def list(self, request, *args, **kwargs):
        query_serializer = serializers.ChecksumFileListQuerySerializer(
            data=self.request.query_params
        )
        query_serializer.is_valid(raise_exception=True)
        url: str = query_serializer.validated_data.get('url')
        collection: int = query_serializer.validated_data.get('collection')

        if url is None and collection is None:
            return super().list(request, *args, **kwargs)

        queryset = self.get_queryset()

        if url is not None:
            queryset = queryset.filter(url=url)
        if collection is not None:
            queryset = queryset.filter(collection=collection)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        method='GET',
        operation_summary='Download ChecksumFile data directly from S3.',
    )
    @action(detail=True)
    def data(self, request, pk=None):
        obj: ChecksumFile = self.get_object()
        return get_file_data_url(obj)

    @swagger_auto_schema(
        query_serializer=serializers.ChecksumFilePathQuerySerializer(),
        responses={200: serializers.ChecksumFilePathsSerializer()},
    )
    @action(detail=False, methods=['GET'])
    def tree(self, request, **kwargs):
        """View ChecksumFiles in a hierarchy, specifying folder/file name with path_prefix."""
        path_prefix: str = self.request.query_params.get('path_prefix') or ''
        folders, files = utils.get_tree(self.get_queryset(), path_prefix)
        return Response(
            serializers.ChecksumFilePathsSerializer({'folders': folders, 'files': files}).data
        )


class SpatialEntryViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.SpatialEntrySerializer
    queryset = models.SpatialEntry.objects.select_subclasses()
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


class SignatureView(BaseRestViewMixin, views.APIView):
    """Generate an expirey URL signature."""

    def post(self, request):
        signer = UserSigner()
        signature = signer.sign(user=self.request.user)
        param = getattr(settings, 'RGD_SIGNED_URL_QUERY_PARAM', 'signature')
        return response.Response({param: signature})
