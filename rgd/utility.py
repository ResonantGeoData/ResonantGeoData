import hashlib
import inspect

from django.db.models import fields
from django.db.models.fields import AutoField
from django.db.models.fields.files import FieldFile, FileField
from django.http import QueryDict
from django.utils.safestring import mark_safe
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import parsers, serializers, viewsets


def compute_checksum(field_file: FieldFile, chunk_num_blocks=128):
    sha256 = hashlib.sha256()
    with field_file.open() as f:
        while chunk := f.read(chunk_num_blocks * sha256.block_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def _link_url(root, name, obj, field):
    if not getattr(obj, field, None):
        return 'No attachment'
    url = getattr(obj, field).url
    return mark_safe('<a href="%s" download>Download</a>' % (url,))


class MultiPartJsonParser(parsers.MultiPartParser):
    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(stream, media_type=media_type, parser_context=parser_context)

        model = None
        qdict = QueryDict('', mutable=True)
        if parser_context and 'view' in parser_context:
            model = parser_context['view'].get_serializer_class().Meta.model
        for key, value in result.data.items():
            # Handle ManytoMany field data, parses lists of comma-separated integers that might be quoted. eg. "1,2"
            if isinstance(getattr(model, key), fields.related_descriptors.ManyToManyDescriptor):
                for val in value.split(','):
                    qdict.update({key: val.strip('"')})
            else:
                qdict.update({key: value})

        return parsers.DataAndFiles(qdict, result.files)


def create_serializer(model, fields=None):
    """Dynamically generate serializer class from model class."""
    if not fields:
        fields = '__all__'

    meta_class = type('Meta', (), {'model': model, 'fields': fields})
    serializer_name = model.__name__ + 'Serializer'
    serializer_class = type(serializer_name, (serializers.ModelSerializer,), {'Meta': meta_class})
    return serializer_class


def create_serializers(models_file, fields=None):
    """Return list of serializer classes from all of the models in the given file."""
    from django.contrib.gis.db import models as base_models

    serializers = []
    for model_name, model in inspect.getmembers(models_file):
        if inspect.isclass(model):
            if model.__bases__[0] == base_models.Model:
                model_fields = {}
                if model_name in fields:
                    model_fields = fields[model_name]
                serializers.append(create_serializer(model, model_fields))
    return serializers


def get_filter_fields(model):
    """
    Return a list of all filterable fields of Model.

    -Takes: Model type
    -Returns: A list of fields as string (excluding ID and file uploading)
    """
    model_fields = model._meta.get_fields()
    fields = []
    for field in model_fields:
        res = str(field).split('.')
        if res[1] == model.__name__ and not isinstance(field, (AutoField, FileField)):
            fields.append(field.name)
    return fields


def create_viewset(serializer, parsers=(MultiPartJsonParser,)):
    """Dynamically create viewset for API router."""
    model = serializer.Meta.model
    model_name = model.__name__
    viewset_class = type(
        model_name + 'ViewSet',
        (viewsets.ModelViewSet,),
        {
            'parser_classes': parsers,
            'queryset': model.objects.all(),
            'serializer_class': serializer,
            'filter_backends': [DjangoFilterBackend],
            'filterset_fields': get_filter_fields(model),
        },
    )
    return viewset_class


def make_serializers(serializer_scope, models):
    """Make serializers for any model that doesn't already have one.

    This should be called after specific serializer classes are created.  Serializers are created named <model_name>Serializer.

    :param serializer_scope: the scope where serializers on the models are defined.  In a serializers.py file, this will be globals().
    :param models: a namespace with defined models for which to create serializers.  This can be a models module.
    """
    from django.contrib.gis.db import models as base_models

    for _model_name, model in inspect.getmembers(models):
        if not inspect.isclass(model):
            continue
        parent = model
        while len(parent.__bases__):
            if base_models.Model in parent.__bases__:
                break
            parent = parent.__bases__[0]
        if base_models.Model in parent.__bases__:
            model_fields = {}
            serializer_class = create_serializer(model, model_fields)
            serializer_name = serializer_class.__name__
            if serializer_name not in serializer_scope:
                serializer_scope[serializer_name] = serializer_class
