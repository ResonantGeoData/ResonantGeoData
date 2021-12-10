import contextlib
from contextlib import contextmanager
from functools import wraps
import hashlib
import io
import logging
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlopen
from uuid import uuid4

import boto3
from botocore import UNSIGNED
from botocore.config import Config
from django.conf import settings
from django.contrib.gis.db.models import Model
from django.core.files import File
from django.db.models.fields.files import FieldFile
from django.utils.safestring import mark_safe
from filelock import FileLock, Timeout
import psutil

try:
    from minio_storage.storage import MinioStorage
except ImportError:
    MinioStorage = None

logger = logging.getLogger(__name__)


def get_temp_dir():
    path = Path(getattr(settings, 'RGD_TEMP_DIR', os.path.join(tempfile.gettempdir(), 'rgd')))
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_dir():
    path = Path(get_temp_dir(), 'file_cache')
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_lock_dir():
    path = Path(get_temp_dir(), 'file_locks')
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_lock(path: Path):
    """Create a file lock under the lock directory."""
    # Computes the hash using Pathlib's hash implementation on absolute path
    sha = hash(path.absolute())
    lock_path = Path(get_lock_dir(), f'{sha}.lock')
    lock = FileLock(lock_path)
    return lock


@contextmanager
def safe_urlopen(url: str, *args, **kwargs):
    with contextlib.closing(urlopen(url, *args, **kwargs)) as remote:
        yield remote


def compute_hash(handle: io.BufferedIOBase, chunk_num_blocks: int = 128):
    sha = hashlib.sha512()
    while chunk := handle.read(chunk_num_blocks * sha.block_size):
        sha.update(chunk)
    return sha.hexdigest()


def compute_checksum_file_field(field_file: FieldFile, chunk_num_blocks: int = 128):
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


def get_s3_client():
    if boto3.session.Session().get_credentials():
        s3 = boto3.client('s3')
    else:
        # No credentials present (often the case in dev), use unsigned requests
        s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    return s3


def _download_url_file_to_stream(
    url: str, dest_stream: io.BufferedIOBase, num_blocks: int = 128, block_size: int = 128
):
    parsed = urlparse(url)
    if parsed.scheme == 's3':
        s3 = get_s3_client()
        s3.download_fileobj(
            parsed.netloc, parsed.path.lstrip('/'), dest_stream, {'RequestPayer': 'requester'}
        )
    else:
        with safe_urlopen(url) as remote:
            while chunk := remote.read(num_blocks * block_size):
                dest_stream.write(chunk)
                dest_stream.flush()


def download_url_file_to_local_path(
    url: str,
    path: str,
    num_blocks: int = 128,
    block_size: int = 128,
) -> Path:
    dest_path = Path(path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, 'wb') as dest_stream:
        _download_url_file_to_stream(url, dest_stream, num_blocks=num_blocks, block_size=block_size)
    return Path(dest_path)


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


def url_file_to_fuse_path(url: str) -> Path:
    # Could raise ValueError within context
    # Assumes `precheck_fuse` was verified prior
    # See https://github.com/ResonantGeoData/ResonantGeoData/issues/237
    parsed = urlparse(url)
    if parsed.scheme == 'https':
        fuse_path = url.replace('https://', '/tmp/rgd/https/') + '..'
    elif parsed.scheme == 'http':
        fuse_path = url.replace('http://', '/tmp/rgd/http/') + '..'
    elif Path('/tmp/rgd/s3/').exists() and parsed.scheme == 's3':
        fuse_path = url.replace('s3://', '/tmp/rgd/s3/') + '..'
    else:
        raise ValueError(f'Scheme {parsed.scheme} not currently handled by FUSE.')
    logger.debug(f'FUSE path: {fuse_path}')
    return Path(fuse_path)


@contextmanager
def patch_internal_presign(f: FieldFile):
    """Create an environment where Minio-based `FieldFile`s construct a locally accessible presigned URL.

    Sometimes the external host differs from the internal host for Minio files (e.g. in development).
    Getting the URL in this context ensures that the presigned URL returns the correct host for the
    odd situation of accessing the file locally.

    Note
    ----
    If concerned regarding concurrent access, see https://github.com/ResonantGeoData/ResonantGeoData/issues/287

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
    workdir = get_temp_dir()
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
def input_output_path_helper(source, output: FieldFile, prefix: str = '', suffix: str = ''):
    """Yield source and output paths between a ChecksumFile and a FileFeild.

    The output path is saved to the output field after yielding.

    """
    filename = prefix + os.path.basename(source.name) + suffix
    with source.yield_local_path() as file_path:
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


def download_field_file_to_local_path(field_file: FieldFile, path: str) -> Path:
    """Download entire FieldFile to disk location.

    This overrides `girder_utils.field_file_to_local_path` to download file to
    local path without a context manager. Cleanup must be handled by caller.

    """
    dest_path = Path(path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    the_path = Path(dest_path)
    with field_file.open('rb'):
        file_obj: File = field_file.file
        if type(file_obj) is File:
            # When file_obj is an actual File, (typically backed by FileSystemStorage),
            # it is already at a stable path on disk.
            # We must symlink it into the desired path
            os.symlink(file_obj.name, dest_path)
            return the_path
        else:
            # When file_obj is actually a subclass of File, it only provides a Python
            # file-like object API. So, it must be copied to a stable path.
            with open(dest_path, 'wb') as dest_stream:
                shutil.copyfileobj(file_obj, dest_stream)
                dest_stream.flush()
            return the_path


def clean_file_cache(override_target=None):
    """Clean the file cache to achieve RGD_TARGET_AVAILABLE_CACHE (Gb).

    Note
    ----
    If above target, this will not do anything.

    Note
    ----
    This is blocking across threads/processes; only one clean can happen at a
    time.

    Return
    ------
    A tuple of the starting and ending free space in bytes.

    """
    cache = get_cache_dir()
    # While free space is not enough, remove directories until all ar gone
    initial = psutil.disk_usage(cache).free
    target = override_target or getattr(settings, 'RGD_TARGET_AVAILABLE_CACHE', 2)
    if psutil.disk_usage(cache).free * 1e-9 >= target:
        # We're above target, so immediately return
        return initial, psutil.disk_usage(cache).free
    # Below target, starting a clean - this is blocking across processes
    cache_lock = get_file_lock(cache)
    with cache_lock:
        logger.debug(f'Cleaning file cache... Starting free space is {initial} bytes.')
        # Sort each directory by mtime
        paths = sorted(Path(cache).iterdir(), key=os.path.getmtime)  # This sorts oldest to latest
        while psutil.disk_usage(cache).free * 1e-9 < target:
            if not len(paths):
                # If we delete everything and still cannot achieve target, warn
                logger.error(
                    f'Target cache free space of {target * 1e9} bytes not achieved when empty.'
                )
                break
            path = paths.pop(0)
            # Check if resource is locked and skip if so
            lock = get_file_lock(path)
            try:
                with lock.acquire(timeout=0):
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                # Remove the lockfile as well
                os.remove(lock.lock_file)
                logger.debug(f'removed: {path}')
            except Timeout:
                # Another task holds the lock on this file/directory: do not delete
                logger.debug(f'File is locked, skipping: {path}')
                pass
    free = psutil.disk_usage(cache).free
    logger.debug(f'Finished cleaning file cache. Available free space is {free} bytes.')
    return initial, free


def purge_file_cache():
    """Completely purge all files from the file cache.

    This should be used with extreme caution, it will delete files that could
    be in use.

    """
    cache = get_temp_dir()
    shutil.rmtree(cache)
    cache = get_cache_dir()  # Return the cache dir so that a fresh directory is created.
    logger.debug(
        f'Purged file cache. Available free space is {psutil.disk_usage(cache).free} bytes.'
    )
    return cache
