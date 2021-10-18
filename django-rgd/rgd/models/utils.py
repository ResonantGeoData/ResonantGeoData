from contextlib import contextmanager
import io
import logging
import tempfile
from typing import List, Union
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from ..utility import compute_checksum_url, compute_hash, get_or_create_no_commit
from .collection import Collection
from .common import ChecksumFile, FileSourceType
from .mixins import Status

logger = logging.getLogger(__name__)


def get_or_create_checksum_file_url(
    url: str,
    collection: Collection = None,
    precompute_url_checksum: bool = False,
    defaults: dict = None,
    **kwargs,
):
    """Get or create ChecksumFile from unique URL and Collection.

    Parameters
    ----------
    precompute_url_checksum : bool
        Precompute the checksum of URL files to prevent duplicate files at different addresses.

    """
    parsed = urlparse(url)
    if parsed.scheme not in ['https', 'http', 's3']:
        raise ValidationError(f'Not a supported URL scheme ({parsed.scheme}) for URL: {url}')
    if precompute_url_checksum:
        checksum = compute_checksum_url(url)
        kwargs.setdefault('checksum', checksum)
    try:
        file_entry = ChecksumFile.objects.get(url=url, collection=collection, **kwargs)
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
        file_entry.collection = collection
        file_entry.save()
        return file_entry, True


def get_or_create_checksumfile_file_field(
    file_handle: io.BufferedIOBase, collection: Collection = None, defaults: dict = None, **kwargs
):
    """Get or create ChecksumFile from an open file handle and Collection."""
    if 'checksum' not in kwargs:
        file_handle.seek(0)
        checksum = compute_hash(file_handle)
        kwargs.setdefault('checksum', checksum)
    file_entry, created = get_or_create_no_commit(
        ChecksumFile, collection=collection, defaults=defaults, **kwargs
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
    collection: Collection = None, precompute_url_checksum=False, defaults: dict = None, **kwargs
):
    """Get or create a ChecksumFile.

    Parameters
    ----------
    precompute_url_checksum : bool
        Precompute the checksum of URL files to prevent duplicate files at different addresses.

    Notes
    -----
    * URL files are only evaluated by their URL and Collection. Use the `url` keyword argument.
    * FILE_FIELD files are evaluated by their checksum value and Collection. Use the `file` keyword argument.

    Since files cannot belong to multiple Collections, we have to validate
    against a Collection. If no Collection is given, then the Collection
    of any existing duplicate file must be None. Otherwise, the file will be
    created to prevent cross-collection permission issues.

    """
    if defaults is None:
        defaults = {}
    if 'collection' in kwargs or 'collection' in defaults:
        raise ValueError('Multiple values of `collection` given.')
    if 'url' in kwargs:
        url = kwargs.pop('url')
        file_entry, created = get_or_create_checksum_file_url(
            url,
            collection=collection,
            precompute_url_checksum=precompute_url_checksum,
            defaults=defaults,
            **kwargs,
        )
    elif 'file' in kwargs:
        file_handle = kwargs.pop('file')
        file_entry, created = get_or_create_checksumfile_file_field(
            file_handle, collection=collection, defaults=defaults, **kwargs
        )
    else:
        raise ValidationError('No URL or file contents passed.')
    return file_entry, created


@contextmanager
def yield_checksumfiles(queryset: Union[QuerySet, List[ChecksumFile]]):
    """Checkout a queryset of ChecksumFile records under a single tempdir.

    This will use the `name` field of each of the files as their relative path
    under the temporary directory.

    """
    names = set()
    files = list(queryset) if isinstance(queryset, QuerySet) else queryset
    with tempfile.TemporaryDirectory() as tempdir:
        for f in files:
            if f.name in names:
                # NOTE: caller's responsibility to handle duplicate names
                logger.error(f'Duplicate `name` for ChecksumFile ({f.pk}: {f.name}). Overriding...')
            # Download each to this directory
            f.download_to_local_path(tempdir)
            names.add(f.name)
        yield tempdir
