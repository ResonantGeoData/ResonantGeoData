from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rgd.models.file import ChecksumFile
from rgd.rest.base import ModelViewSet
from rgd.rest.mixins import TaskEventViewSetMixin
from rgd.utility import get_file_data_url
from rgd_3d import models, serializers


class Mesh3DViewSet(ModelViewSet, TaskEventViewSetMixin):
    serializer_class = serializers.Mesh3DSerializer
    queryset = models.Mesh3D.objects.all()

    @action(
        detail=True,
        serializer_class=serializers.Mesh3DDataSerializer,
    )
    def base64(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class Tiles3DViewSet(ModelViewSet):
    queryset = models.Tiles3D.objects.all()

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve', 'status'}:
            return serializers.Tiles3DMetaSerializer
        return serializers.Tiles3DSerializer

    def get_queryset(self):
        if self.action in {'list', 'retrieve', 'status'}:
            return models.Tiles3DMeta.objects.all()
        return models.Tiles3D.objects.all()

    @swagger_auto_schema(responses={302: openapi.Response('Redirect to file download')})
    @action(detail=True, methods=['GET'], url_path='file/(?P<name>.+)')
    def file(self, request: Request, pk: str, name: str):
        """Download a file from a 3D tiles FileSet."""
        tiles3d_set: models.Tiles3D = get_object_or_404(models.Tiles3D, pk=pk)
        checksum_file: ChecksumFile = get_object_or_404(
            tiles3d_set.json_file.file_set.files, name=name
        )
        return get_file_data_url(checksum_file)
