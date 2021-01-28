from contextlib import contextmanager
import hashlib
import inspect
import os
from pathlib import Path, PurePath
import tempfile
from typing import Generator
from urllib.request import urlopen

from django.db.models import fields
from django.db.models.fields import AutoField
from django.db.models.fields.files import FieldFile, FileField
from django.http import QueryDict
from django.utils.safestring import mark_safe
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import parsers, serializers, viewsets


def _compute_hash(handle, chunk_num_blocks):
    sha = hashlib.sha512()
    while chunk := handle.read(chunk_num_blocks * sha.block_size):
        sha.update(chunk)
    return sha.hexdigest()


def compute_checksum_file(field_file: FieldFile, chunk_num_blocks=128):
    with field_file.open() as f:
        hash = _compute_hash(f, chunk_num_blocks)
    return hash


def compute_checksum_url(url: str, chunk_num_blocks=128):
    remote = urlopen(url)
    return _compute_hash(remote, chunk_num_blocks)


def _link_url(root, name, obj, field):
    if not getattr(obj, field, None):
        return 'No attachment'
    attr = getattr(obj, field)
    if callable(attr):
        url = attr()
    else:
        url = attr.url
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


def get_or_create_no_commit(model, defaults=None, **kwargs):
    try:
        return model.objects.get(**kwargs), False
    except model.DoesNotExist:
        if not defaults:
            defaults = {}
        defaults.update(kwargs)
        return model(**defaults), True


@contextmanager
def url_file_to_local_path(url: str, num_blocks=128, block_size=128) -> Generator[Path, None, None]:
    # Eventually we need to re-work this for https://github.com/ResonantGeoData/ResonantGeoData/issues/237
    remote = urlopen(url)
    field_file_basename = PurePath(os.path.basename(url)).name
    with tempfile.NamedTemporaryFile('wb', suffix=field_file_basename) as dest_stream:
        while chunk := remote.read(num_blocks * block_size):
            dest_stream.write(chunk)
            dest_stream.flush()
        yield Path(dest_stream.name)
