import contextlib
from contextlib import contextmanager
from functools import wraps
import hashlib
import io
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
from django.contrib.gis.db.models import Model
from django.db.models.fields.files import FieldFile
from django.utils.safestring import mark_safe

try:
    from minio_storage.storage import MinioStorage
except ImportError:
    MinioStorage = None

logger = logging.getLogger(__name__)


@contextmanager
def safe_urlopen(url: str, *args, **kwargs):
    with contextlib.closing(urlopen(url, *args, **kwargs)) as remote:
        yield remote


def compute_hash(handle: io.BufferedIOBase, chunk_num_blocks: int = 128):
    sha = hashlib.sha512()
    while chunk := handle.read(chunk_num_blocks * sha.block_size):
        sha.update(chunk)
    return sha.hexdigest()


def compute_checksum_file(field_file: FieldFile, chunk_num_blocks: int = 128):
    with field_file.open() as f:
        return compute_hash(f, chunk_num_blocks)


def compute_checksum_url(url: str, chunk_num_blocks: int = 128):
    with safe_urlopen(url) as remote:
        return compute_hash(remote, chunk_num_blocks)


def _link_url(obj: Model, field: str):
    if not getattr(obj, field, None):
        return 'No attachment'
    attr = getattr(obj, field)
    if callable(attr):
        url = attr()
    else:
        url = attr.url
    return mark_safe(f'<a href="{url}" download>Download</a>')


def get_or_create_no_commit(model: Model, defaults: dict = None, **kwargs):
    try:
        return model.objects.get(**kwargs), False
    except model.DoesNotExist:
        if not defaults:
            defaults = {}
        defaults.update(kwargs)
        return model(**defaults), True


@contextmanager
def url_file_to_local_path(
    url: str, num_blocks: int = 128, block_size: int = 128, override_name: str = None
) -> Generator[Path, None, None]:
    with safe_urlopen(url) as remote:
        if override_name:
            suffix = override_name
        else:
            suffix = PurePath(os.path.basename(url)).name
        with tempfile.NamedTemporaryFile('wb', suffix=suffix) as dest_stream:
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
