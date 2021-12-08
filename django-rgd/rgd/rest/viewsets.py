from django.conf import settings
from django.http import HttpResponseRedirect
from drf_yasg.utils import swagger_auto_schema
from rest_framework import response, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rgd import models, serializers
from rgd.filters import SpatialEntryFilter
from rgd.rest.base import ModelViewSet, ReadOnlyModelViewSet

from .authentication import UserSigner
from .mixins import BaseRestViewMixin, TaskEventViewSetMixin


class CollectionViewSet(ModelViewSet):
    serializer_class = serializers.CollectionSerializer
    queryset = models.Collection.objects.all()


class CollectionPermissionViewSet(ModelViewSet):
    serializer_class = serializers.CollectionPermissionSerializer
    queryset = models.CollectionPermission.objects.all()


class ChecksumFileViewSet(ModelViewSet, TaskEventViewSetMixin):
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

    @swagger_auto_schema(
        query_serializer=serializers.ChecksumFilePathQuerySerializer(),
        responses={200: serializers.ChecksumFilePathsSerializer()},
    )
    @action(detail=False, methods=['GET'])
    def tree(self, request, **kwargs):
        """View ChecksumFiles in a hierarchy, specifying folder/file name with path_prefix."""
        path_prefix: str = self.request.query_params.get('path_prefix') or ''
        qs = self.get_queryset().filter(name__startswith=path_prefix)

        folders: dict[str, dict] = {}
        files: dict[str, models.ChecksumFile] = {}

        for file in qs:
            file: models.ChecksumFile

            # Get the remainder of the path after path_prefix
            base_path: str = file.name[len(path_prefix) :].strip('/')

            # Since we stripped slashes, any remaining slashes indicate a folder
            folder_index = base_path.find('/')
            is_folder = folder_index >= 0

            if not is_folder:
                # Ensure base_path is entire filename
                base_path = file.name[file.name.rfind('/') + 1 :]
                files[base_path] = file
            else:
                base_path = base_path[:folder_index]
                entry = folders.get(base_path)
                fixed_file_size = file.size or 0
                url_file_as_int = 1 - int(bool(file.size))

                # Either create new folder entry, or add to existing folder
                if entry is None:
                    # New folder entry
                    folders[base_path] = {
                        'known_size': fixed_file_size,
                        'num_files': 1,
                        'num_url_files': url_file_as_int,
                        'created': file.created,
                        'modified': file.modified,
                    }
                else:
                    # Add to existing folder
                    entry['known_size'] += fixed_file_size
                    entry['num_files'] += 1
                    entry['num_url_files'] += url_file_as_int
                    entry['created'] = min(entry['created'], file.created)  # earliest
                    entry['modified'] = max(entry['modified'], file.modified)  # latest

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
