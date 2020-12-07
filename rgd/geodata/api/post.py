from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.generics import CreateAPIView

from ..models.imagery import ConvertedImageFile, ImageEntry
from .. import serializers


class ConvertImageToCog(CreateAPIView):
    serializer_class = serializers.ConvertedImageFileSerializer

    # TODO this is supposed to work but it doesn't
    #      see: https://drf-yasg.readthedocs.io/en/stable/custom_spec.html#the-swagger-auto-schema-decorator
    @swagger_auto_schema(
        operation_summary='Convert an ImageEntry to specified format.',
        operation_description='Convert an ImageEntry with given PK to a specified format as a new ConvertedImageFile. Currently only Cloud Optimized GeoTIFF (COG) is supported.',
    )
    def create(self, request, source_image, format=None):
        # TODO: use format option if supporting things other than COG.
        img = ImageEntry.objects.get(id=source_image)
        # Do not create duplicate conversions
        try:
            c = img.convertedimagefile
        except ObjectDoesNotExist:
            c = ConvertedImageFile()
            c.source_image = img
        c.save()
        return JsonResponse({'converted_pk': c.pk})
