from django.http import HttpResponseRedirect
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from rgd.permissions import check_read_perm
from rgd.rest.download import _get_status_response

from rgd_imagery import models


@swagger_auto_schema(
    method='GET',
    operation_summary='Download the associated ImageFile data for this ImageEntry directly from S3.',
)
@api_view(['GET'])
def download_image_entry_file(request, pk):
    instance = models.imagery.ImageEntry.objects.get(pk=pk)
    check_read_perm(request.user, instance)
    url = instance.image_file.imagefile.file.get_url()
    return HttpResponseRedirect(url)


@swagger_auto_schema(
    method='GET',
    operation_summary='Download the associated ChecksumFile data for this ConvertedImageFile directly from S3.',
)
@api_view(['GET'])
def download_cog_file(request, pk):
    instance = models.imagery.ConvertedImageFile.objects.get(pk=pk)
    check_read_perm(request.user, instance)
    af_id = instance.converted_file.id
    instance = models.common.ChecksumFile.objects.get(pk=af_id)
    return HttpResponseRedirect(instance.get_url())


@swagger_auto_schema(
    method='GET',
    operation_summary='Check the status of SubsampledImage.',
)
@api_view(['GET'])
def get_status_subsampled_image(request, pk):
    """Get the status of any SubsampledImage model."""
    return _get_status_response(request, 'SubsampledImage', pk)
