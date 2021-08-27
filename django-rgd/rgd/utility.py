import contextlib
from contextlib import contextmanager
from functools import wraps
import hashlib
import inspect
import logging
import os
from pathlib import Path, PurePath
import tempfile
from typing import Any, Generator
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen
from uuid import uuid4

from django.conf import settings
from django.db.models import fields
from django.db.models.fields import AutoField
from django.db.models.fields.files import FieldFile, FileField
from django.http import QueryDict
from django.utils.safestring import mark_safe
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import parsers, serializers, viewsets

try:
    from minio_storage.storage import MinioStorage
except ImportError:
    MinioStorage = None

logger = logging.getLogger(__name__)


@contextmanager
def safe_urlopen(url, *args, **kwargs):
    with contextlib.closing(urlopen(url, *args, **kwargs)) as remote:
        yield remote


def _compute_hash(handle, chunk_num_blocks):
    sha = hashlib.sha512()
    while chunk := handle.read(chunk_num_blocks * sha.block_size):
        sha.update(chunk)
    return sha.hexdigest()


def compute_checksum_file(field_file: FieldFile, chunk_num_blocks=128):
    with field_file.open() as f:
        return _compute_hash(f, chunk_num_blocks)


def compute_checksum_url(url: str, chunk_num_blocks=128):
    with safe_urlopen(url) as remote:
        return _compute_hash(remote, chunk_num_blocks)


def _link_url(obj, field):
    if not getattr(obj, field, None):
        return 'No attachment'
    attr = getattr(obj, field)
    if callable(attr):
        url = attr()
    else:
        url = attr.url
    return mark_safe(f'<a href="{url}" download>Download</a>')


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
    return type(serializer_name, (serializers.ModelSerializer,), {'Meta': meta_class})


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
    return type(
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
    with safe_urlopen(url) as remote:
        field_file_basename = PurePath(os.path.basename(url)).name
        with tempfile.NamedTemporaryFile('wb', suffix=field_file_basename) as dest_stream:
            while chunk := remote.read(num_blocks * block_size):
                dest_stream.write(chunk)
                dest_stream.flush()
            yield Path(dest_stream.name)


def precheck_fuse(url: str) -> bool:
    try:
        import simple_httpfs  # noqa
    except (ImportError, EnvironmentError):
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ['https', 'http']:
        return False
    try:
        # The FUSE lib will not catch URL errors
        with safe_urlopen(url) as _:
            pass
    except HTTPError:
        return False
    return True


@contextmanager
def url_file_to_fuse_path(url: str) -> Generator[Path, None, None]:
    # Could raise ValueError within context
    # Assumes `precheck_fuse` was verified prior
    # See https://github.com/ResonantGeoData/ResonantGeoData/issues/237
    parsed = urlparse(url)
    if parsed.scheme == 'https':
        fuse_path = url.replace('https://', '/tmp/rgd/https/') + '..'
    elif parsed.scheme == 'http':
        fuse_path = url.replace('http://', '/tmp/rgd/http/') + '..'
    else:
        raise ValueError(f'Scheme {parsed.scheme} not currently handled.')
    logger.info(f'FUSE path: {fuse_path}')
    yield Path(fuse_path)


@contextmanager
def patch_internal_presign(f: FieldFile):
    """Create an environment where Minio-based `FieldFile`s construct a locally accessible presigned URL.

    Sometimes the external host differs from the internal host for Minio files (e.g. in development).
    Getting the URL in this context ensures that the presigned URL returns the correct host for the
    odd situation of accessing the file locally.
    """
    if (
        MinioStorage is not None
        and isinstance(f.storage, MinioStorage)
        and getattr(settings, 'MINIO_STORAGE_MEDIA_URL', None) is not None
    ):
        original_base_url = f.storage.base_url
        try:
            f.storage.base_url = None
            yield
        finally:
            f.storage.base_url = original_base_url
        return
    yield


@contextmanager
def output_path_helper(filename: str, output: FieldFile):
    workdir = getattr(settings, 'GEODATA_WORKDIR', None)
    with tempfile.TemporaryDirectory(dir=workdir) as tmpdir:
        output_path = os.path.join(tmpdir, filename)
        try:
            # Yield the path for the user to perform a task
            yield output_path
        except Exception as e:
            raise e
        else:
            # Save the file contents to the output field only on success
            with open(output_path, 'rb') as f:
                output.save(os.path.basename(output_path), f)


@contextmanager
def input_output_path_helper(
    source, output: FieldFile, prefix: str = '', suffix: str = '', vsi: bool = False
):
    """Yield source and output paths between a ChecksumFile and a FileFeild.

    The output path is saved to the output field after yielding.

    """
    filename = prefix + os.path.basename(source.name) + suffix
    with source.yield_local_path(vsi=vsi) as file_path:
        filename = prefix + os.path.basename(source.name) + suffix
        with output_path_helper(filename, output) as output_path:
            try:
                # Yield the paths for the user to perform a task
                yield (file_path, output_path)
            except Exception as e:
                raise e
            else:
                # Save the file contents to the output field only on success
                with open(output_path, 'rb') as f:
                    output.save(os.path.basename(output_path), f)


def uuid_prefix_filename(instance: Any, filename: str):
    """Use a variable in settings to add a prefix to the path and keep the random uuid."""
    prefix = getattr(settings, 'RGD_FILE_FIELD_PREFIX', None)
    if prefix:
        return f'{prefix}/{uuid4()}/{filename}'
    return f'{uuid4()}/{filename}'


def skip_signal():
    """Skip the signal on an instance-basis."""

    def _skip_signal(signal_func):
        @wraps(signal_func)
        def _decorator(sender, instance, *args, **kwargs):
            if hasattr(instance, 'skip_signal') and instance.skip_signal:
                return None
            return signal_func(sender, instance, *args, **kwargs)

        return _decorator

    return _skip_signal
