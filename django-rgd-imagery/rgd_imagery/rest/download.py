from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rgd.permissions import check_read_perm
from rgd_imagery import models


@swagger_auto_schema(
    method='GET',
    operation_summary='Download the associated Image data for this Image directly from S3.',
)
@api_view(['GET'])
def download_image_file(request, pk):
    instance = get_object_or_404(models.Image, pk=pk)
    check_read_perm(request.user, instance)
    url = instance.file.get_url()
    return HttpResponseRedirect(url)
