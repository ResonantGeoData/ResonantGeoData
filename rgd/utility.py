from contextlib import contextmanager
import datetime
import hashlib
import inspect
from pathlib import Path, PurePath
import shutil
import tempfile
from typing import Generator

from django.core.files import File
from django.db.models import fields
from django.db.models.fields import AutoField
from django.db.models.fields.files import FieldFile, FileField
from django.http import QueryDict
from django.utils.safestring import mark_safe
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import parsers, serializers, viewsets
from storages.backends.s3boto3 import S3Boto3StorageFile


@contextmanager
def _field_file_to_local_path(field_file: FieldFile) -> Generator[Path, None, None]:
    with field_file.open('rb'):
        file_obj: File = field_file.file

        if not Path(file_obj.name).exists() or isinstance(file_obj, S3Boto3StorageFile):
            field_file_basename = PurePath(field_file.name).name
            with tempfile.NamedTemporaryFile('wb', suffix=field_file_basename) as dest_stream:
                shutil.copyfileobj(file_obj, dest_stream)
                dest_stream.flush()

                yield Path(dest_stream.name)
        else:
            yield Path(file_obj.name)


def compute_checksum(file_path, chunk_num_blocks=128):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_num_blocks * sha256.block_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def _link_url(root, name, obj, field):
    if not getattr(obj, field, None):
        return 'No attachment'
    url = getattr(obj, field).url
    if '//minio:' in url:
        url = '/api/%s/download/%s/%s/%s' % (root, name, obj.id, field)
    return mark_safe('<a href="%s" download>Download</a>' % (url,))


def parse_time_params(time_params):
    start, end = None, None
    time, diff = None, None

    if 'startdate' in time_params:
        start = time_params['startdate']
    if 'starttime' in time_params:
        if start:
            start = start.replace(
                hour=time_params['starttime'].hour, minute=time_params['starttime'].minute
            )
        else:
            # Defaults to current day if no date is given
            start = time_params['starttime']

    if 'enddate' in time_params:
        end = time_params['enddate']
    if 'endtime' in time_params:
        if end:
            end = end.replace(
                hour=time_params['endtime'].hour, minute=time_params['endtime'].minute
            )
        elif start:
            # Takes start's date if given
            end = start.replace(
                hour=time_params['endtime'].hour, minute=time_params['endtime'].minute
            )
        else:
            # Defaults to current day if no date is given
            end = time_params['endtime']

    if start and end:
        diff = (end - start) / 2
        time = start + diff
    elif start:
        # Spans from start datetime given to end of given day
        next_day = datetime.datetime(start.year, start.month, start.day) + datetime.timedelta(
            days=1
        )
        diff = (next_day - start) / 2
        time = start + diff
    elif end:
        # Spans from the start of the given day to end datetime
        past_day = datetime.datetime(end.year, end.month, end.day)
        diff = (end - past_day) / 2
        time = end - diff

    return (time, diff)


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
