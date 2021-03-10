from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404  # , render
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from rgd.geodata import models
from rgd.geodata.permissions import check_read_perm


@swagger_auto_schema(
    method='GET',
    operation_summary='Download ChecksumFile data directly from S3.',
)
@api_view(['GET'])
def download_checksum_file(request, pk):
    instance = models.common.ChecksumFile.objects.get(pk=pk)
    check_read_perm(request.user, instance)
    reponse = HttpResponseRedirect(instance.get_url())
    return reponse


@swagger_auto_schema(
    method='GET',
    operation_summary='Download the associated ImageFile data for this ImageEntry directly from S3.',
)
@api_view(['GET'])
def download_image_entry_file(request, pk):
    instance = models.imagery.ImageEntry.objects.get(pk=pk)
    check_read_perm(request.user, instance)
    url = instance.image_file.file.get_url()
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


def _get_status_response(request, model, pk):
    model_class = ''.join([part[:1].upper() + part[1:] for part in model.split('_')])
    if not hasattr(models, model_class):
        raise AttributeError('No such model (%s)' % model)
    instance = get_object_or_404(getattr(models, model_class), pk=pk)
    check_read_perm(request.user, instance)
    if not hasattr(instance, 'status'):
        raise AttributeError(f'Model ({model}) has no attribute (status).')
    data = {
        'pk': instance.pk,
        'model': model,
        'status': instance.status,
    }
    return Response(data)


@swagger_auto_schema(
    method='GET',
    operation_summary='Check the status.',
)
@api_view(['GET'])
def get_status(request, model, pk):
    """Get the status of any TaskEventMixin model."""
    return _get_status_response(request, model, pk)


@swagger_auto_schema(
    method='GET',
    operation_summary='Check the status of SubsampledImage.',
)
@api_view(['GET'])
def get_status_subsampled_image(request, pk):
    """Get the status of any SubsampledImage model."""
    return _get_status_response(request, 'SubsampledImage', pk)
