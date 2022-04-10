from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django_large_image.rest import LargeImageDetailMixin
from rest_framework.request import Request
from rgd.rest import CACHE_TIMEOUT
from rgd.rest.authentication import SignedURLAuthentication
from rgd.rest.base import ModelViewSet
from rgd_imagery import models, serializers
from rgd_imagery.models import Image


class TilesViewSet(ModelViewSet, LargeImageDetailMixin):
    serializer_class = serializers.ImageSerializer
    queryset = models.Image.objects.all()
    authentication_classes = ModelViewSet.authentication_classes + [
        SignedURLAuthentication,
    ]

    def get_path(self, request: Request, pk: int) -> str:
        """Return the built tile source."""
        # get image_entry from cache
        image_cache_key = f'large_image_tile:image_{pk}'
        if (image_entry := cache.get(image_cache_key, None)) is None:
            image_entry = get_object_or_404(Image.objects.select_related('file'), pk=pk)
            cache.set(image_cache_key, image_entry, CACHE_TIMEOUT)

        # check authentication
        sentinel = object()
        auth_cache_key = f'large_image_tile:image_{pk}:user_{request.user.pk}'
        if cache.get(auth_cache_key, sentinel) is sentinel:
            self.check_object_permissions(request, image_entry)
            cache.set(auth_cache_key, None, CACHE_TIMEOUT)

        with image_entry.file.yield_local_path(yield_file_set=True) as file_path:
            # NOTE: We ran into issues using VSI paths with some image formats (NITF)
            #       this now requires the images be a local path on the file system.
            #       For URL files, this is done through FUSE but for S3FileField
            #       files, we must download the entire file to the local disk.
            # NOTE: yield_file_set=True in case there are header files
            return str(file_path)
