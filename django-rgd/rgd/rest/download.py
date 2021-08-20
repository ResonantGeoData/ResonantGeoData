from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404  # , render
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rgd import models
from rgd.permissions import check_read_perm, get_model


@swagger_auto_schema(
    method='GET',
    operation_summary='Download ChecksumFile data directly from S3.',
)
@api_view(['GET'])
def download_checksum_file(request, pk):
    instance = get_object_or_404(models.ChecksumFile, pk=pk)
    check_read_perm(request.user, instance)
    return HttpResponseRedirect(instance.get_url())


def _get_status_response(request, model, pk):
    model_class = get_model(model)
    if not model_class:
        raise AttributeError(f'Model ({model}) does not exist.')
    instance = get_object_or_404(model_class, pk=pk)
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
