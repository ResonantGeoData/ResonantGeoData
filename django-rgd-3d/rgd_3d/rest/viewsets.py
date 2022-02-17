from django.db.models.fields.files import FieldFile
from django.shortcuts import redirect
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rgd.models.file import ChecksumFile
from rgd.rest.base import ModelViewSet
from rgd.rest.mixins import TaskEventViewSetMixin
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
    serializer_class = serializers.Tiles3DSerializer
    queryset = models.Tiles3D.objects.all()

    @swagger_auto_schema(responses={302: openapi.Response('Redirect to file download')})
    @action(detail=True, methods=['GET'], url_path='file/(?P<name>.+)')
    def file(self, request: Request, pk: str, name: str):
        """Download a file from a 3D tiles FileSet."""
        tiles3d_set: models.Tiles3D = get_object_or_404(models.Tiles3D, pk=pk)
        checksum_file: ChecksumFile = get_object_or_404(
            tiles3d_set.json_file.file_set.files, name=name
        )
        file: FieldFile = checksum_file.file
        return redirect(file.url, permanent=False)
