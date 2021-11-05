from contextlib import contextmanager
import io
import logging
from pathlib import Path
from typing import List, Union
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from filelock import FileLock

from ..utility import compute_checksum_url, compute_hash, get_or_create_no_commit
from .file import ChecksumFile, FileSourceType
from .fileset import FileSet
from .mixins import Status

logger = logging.getLogger(__name__)


def get_or_create_checksum_file_url(
    url: str,
    file_set: FileSet = None,
    precompute_url_checksum: bool = False,
    defaults: dict = None,
    **kwargs,
):
    """Get or create ChecksumFile from unique URL and FileSet.

    Parameters
    ----------
    precompute_url_checksum : bool
        Precompute the checksum of URL files to prevent duplicate files at different addresses.

    """
    if defaults is None:
        defaults = {}
    parsed = urlparse(url)
    if parsed.scheme not in ['https', 'http', 's3']:
        raise ValidationError(f'Not a supported URL scheme ({parsed.scheme}) for URL: {url}')
    if precompute_url_checksum:
        checksum = compute_checksum_url(url)
        kwargs.setdefault('checksum', checksum)
    try:
        file_entry = ChecksumFile.objects.get(url=url, file_set=file_set, **kwargs)
        if file_entry.status != Status.SUCCEEDED and file_entry.status != Status.SKIPPED:
            # If in a failed state, rerun tasks
            file_entry.save()
        return file_entry, False
    except ChecksumFile.DoesNotExist:
        defaults = defaults.copy()
        defaults.update(kwargs)
        file_entry = ChecksumFile(**defaults)
        file_entry.url = url
        file_entry.type = FileSourceType.URL
        file_entry.file_set = file_set
        file_entry.save()
        return file_entry, True


def get_or_create_checksumfile_file_field(
    file_handle: io.BufferedIOBase, file_set: FileSet = None, defaults: dict = None, **kwargs
):
    """Get or create ChecksumFile from an open file handle and FileSet."""
    if 'checksum' not in kwargs:
        file_handle.seek(0)
        checksum = compute_hash(file_handle)
        kwargs.setdefault('checksum', checksum)
    file_entry, created = get_or_create_no_commit(
        ChecksumFile, file_set=file_set, defaults=defaults, **kwargs
    )
    if created:
        # Since we already computed the checksum, prevent tasks from recomputing
        file_entry.skip_signal = True
        file_handle.seek(0)
        file_entry.file.save('test', file_handle)
        file_entry.save()
        file_entry.skip_signal = False
    return file_entry, created


def get_or_create_checksumfile(
    file_set: FileSet = None, precompute_url_checksum=False, defaults: dict = None, **kwargs
):
    """Get or create a ChecksumFile.

    Parameters
    ----------
    precompute_url_checksum : bool
        Precompute the checksum of URL files to prevent duplicate files at different addresses.

    Notes
    -----
    * URL files are only evaluated by their URL and FileSet. Use the `url` keyword argument.
    * FILE_FIELD files are evaluated by their checksum value and FileSet. Use the `file` keyword argument.

    Since files cannot belong to multiple FileSets, we have to validate
    against a FileSet. If no FileSet is given, then the FileSet
    of any existing duplicate file must be None. Otherwise, the file will be
    created to prevent cross-fileset/collection permission issues.

    """
    if defaults is None:
        defaults = {}
    if 'file_set' in kwargs or 'file_set' in defaults:
        raise ValueError('Multiple values of `file_set` given.')
    if 'url' in kwargs:
        url = kwargs.pop('url')
        file_entry, created = get_or_create_checksum_file_url(
            url,
            file_set=file_set,
            precompute_url_checksum=precompute_url_checksum,
            defaults=defaults,
            **kwargs,
        )
    elif 'file' in kwargs:
        file_handle = kwargs.pop('file')
        file_entry, created = get_or_create_checksumfile_file_field(
            file_handle, file_set=file_set, defaults=defaults, **kwargs
        )
    else:
        raise ValidationError('No URL or file contents passed.')
    return file_entry, created


@contextmanager
def yield_checksumfiles(queryset: Union[QuerySet, List[ChecksumFile]], directory: str):
    """Checkout a queryset of ChecksumFile records under a single directory.

    This will use the `name` field of each of the files as their relative path
    under the temporary directory.

    Please note that this uses a contextmanager to acquire a lock on the
    directory to make sure the files are not automatically cleaned up by
    other threads or processes.

    """
    files = list(queryset) if isinstance(queryset, QuerySet) else queryset
    # Touch the directory to update the mtime
    directory = Path(directory)
    directory.touch()
    # Acquire a lock on the directory so that it isn't cleaned up
    lock_file_path = f'{directory}.lock'
    lock = FileLock(lock_file_path)
    lock.acquire()
    # Download each file to the directory and yeild it so that the lock can be released when done
    try:
        names = set()
        # TODO: implement a FUSE interface
        for file in files:
            if file.name in names:
                # NOTE: caller's responsibility to handle duplicate names
                logger.error(
                    f'Duplicate `name` for ChecksumFile ({file.pk}: {file.name}). Overwriting...'
                )
            names.add(file.name)
            file.download_to_local_path(directory=directory)
        yield directory
    finally:
        lock.release()
