import os

from django.db.models.fields.files import FieldFile
from django.http import HttpResponse
from django.shortcuts import get_object_or_404  # , render
from django.utils.encoding import smart_str
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view

from rgd.geodata import models


@swagger_auto_schema(
    method='GET',
    operation_summary='Download a model file',
    operation_description='Download a model file through the server instead of from the assetstore',
)
@api_view(['GET'])
def download_file(request, model, id, field):
    model_class = ''.join([part[:1].upper() + part[1:] for part in model.split('_')])
    if not hasattr(models, model_class):
        raise Exception('No such model (%s)' % model)
    model_inst = get_object_or_404(getattr(models, model_class), pk=id)
    if not isinstance(getattr(model_inst, field, None), FieldFile):
        raise Exception('No such file (%s)' % field)
    file = getattr(model_inst, field)
    filename = os.path.basename(file.name)
    if not filename:
        filename = '%s_%s_%s.dat' % (model, id, field)
    mimetype = getattr(
        model_inst,
        '%s_mimetype' % field,
        'text/plain' if field == 'log' else 'application/octet-stream',
    )
    response = HttpResponse(file.chunks(), content_type=mimetype)
    response['Content-Disposition'] = smart_str(u'attachment; filename=%s' % filename)
    if len(file) is not None:
        response['Content-Length'] = len(file)
    return response
