from django.http import JsonResponse
from drf_yasg2.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from ..models.imagery import ConvertedImageFile


@swagger_auto_schema(
    method='GET',
    operation_summary='Get the status of a ConvertedImageFile by PK.',
)
@api_view(['GET'])
def get_status_converted_image_file(request, pk):
    c = ConvertedImageFile.objects.get(id=pk)
    data = {
        'pk': c.pk,
        'source_image_pk': c.source_image.pk,
        'status': c.status,
        'failure_reason': c.failure_reason,
    }
    return JsonResponse(data)
