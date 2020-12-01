from django.http import JsonResponse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from ..models.imagery import ConvertedImageFile, ImageEntry


@swagger_auto_schema(
    method='POST',
    operation_summary='Convert an ImageEntry to specified format.',
    operation_description='Convert an ImageEntry with given PK to a specified format as a new ConvertedImageFile. Currently only Cloud Optimized GeoTIFF (COG) is supported.',
)
@api_view(['POST'])
def convert_image_to_cog(request, pk, format=None):
    # TODO: use format option if supporting things other than COG.
    img = ImageEntry.objects.get(id=pk)
    c = ConvertedImageFile()
    c.source_image = img
    c.save()
    return JsonResponse({'converted_pk': c.pk})
