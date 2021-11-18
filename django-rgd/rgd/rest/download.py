from django.shortcuts import get_object_or_404  # , render
from rest_framework.response import Response
from rgd.permissions import check_read_perm, get_model


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
