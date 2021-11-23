from contextlib import contextmanager
import logging
import os
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse

from crum import get_current_user
from django.conf import settings
from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from rgd.utility import (
    _link_url,
    clean_file_cache,
    compute_checksum_file_field,
    compute_checksum_url,
    compute_hash,
    download_field_file_to_local_path,
    download_url_file_to_local_path,
    get_cache_dir,
    get_file_lock,
    patch_internal_presign,
    precheck_fuse,
    safe_urlopen,
    url_file_to_fuse_path,
    uuid_prefix_filename,
)
from s3_file_field import S3FileField

from .. import tasks
from .collection import Collection
from .fileset import FileSet
from .mixins import TaskEventMixin

logger = logging.getLogger(__name__)


class FileSourceType(models.IntegerChoices):
    FILE_FIELD = 1, 'FileField'
    URL = 2, 'URL'


class ChecksumFile(TimeStampedModel, TaskEventMixin):
    """The main class for user-uploaded files.

    This has support for manually uploading files or specifying a URL to a file
    (for example in an existing S3 bucket). This broadly supports ``http<s>://``
    URLs to file resources as well as ``s3://`` as long as the node the app is
    running on is provisioned to access that S3 bucket.

    """

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)
    checksum = models.CharField(max_length=128)  # sha512
    validate_checksum = models.BooleanField(
        default=False
    )  # a flag to validate the checksum against the saved checksum
    last_validation = models.BooleanField(default=True)
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        related_name='%(class)ss',
        related_query_name='%(class)ss',
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, default=None, on_delete=models.SET_NULL
    )
    file_set = models.ForeignKey(FileSet, null=True, blank=True, on_delete=models.SET_NULL)

    type = models.IntegerField(choices=FileSourceType.choices, default=FileSourceType.FILE_FIELD)
    file = S3FileField(null=True, blank=True, upload_to=uuid_prefix_filename)
    url = models.TextField(null=True, blank=True)

    task_funcs = (tasks.task_checksum_file_post_save,)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name='%(app_label)s_%(class)s_file_source_value_matches_type',
                check=(
                    models.Q(
                        models.Q(type=FileSourceType.FILE_FIELD, file__regex=r'.+')
                        & models.Q(models.Q(url__in=['', None]) | models.Q(url__isnull=True))
                    )
                    | models.Q(
                        models.Q(type=FileSourceType.URL)
                        & models.Q(models.Q(url__isnull=False) & models.Q(url__regex=r'.+'))
                        & models.Q(models.Q(file__in=['', None]) | models.Q(file__isnull=True))
                    )
                ),
            ),
            models.UniqueConstraint(
                fields=['file_set', 'name'],
                name='unique_name',
            ),
        ]

    @property
    def basename(self):
        return os.path.basename(self.name)

    @property
    def size(self):
        # Ensure safe check of self.file
        try:
            return self.file.size
        except ValueError:
            return None

    def get_checksum(self):
        """Compute a new checksum without saving it."""
        if self.type == FileSourceType.FILE_FIELD:
            return compute_checksum_file_field(self.file)
        elif self.type == FileSourceType.URL:
            parsed = urlparse(self.url)
            if parsed.scheme in ['https', 'http']:
                return compute_checksum_url(self.url)
            else:
                with self.yield_local_path() as path:
                    with open(path, 'rb') as f:
                        return compute_hash(f)
        else:
            raise NotImplementedError(f'Type ({self.type}) not supported.')

    def update_checksum(self):
        self.checksum = self.get_checksum()
        # Simple update save - not full save
        super(ChecksumFile, self).save(
            update_fields=[
                'checksum',
            ]
        )

    def validate(self):
        previous = self.checksum
        self.update_checksum()
        self.last_validation = self.checksum == previous
        # Simple update save - not full save
        super(ChecksumFile, self).save(
            update_fields=[
                'last_validation',
            ]
        )
        return self.last_validation

    def post_save_job(self):
        if not self.checksum or self.validate_checksum:
            if self.validate_checksum:
                self.validate()
            else:
                self.update_checksum()
            # Reset the user flags
            self.validate_checksum = False
            # Simple update save - not full save
            self.save(
                update_fields=[
                    'checksum',
                    'last_validation',
                    'validate_checksum',
                ]
            )

    def save(self, *args, **kwargs):
        if not self.name:
            if self.type == FileSourceType.FILE_FIELD and self.file.name:
                self.name = os.path.basename(self.file.name)
            elif self.type == FileSourceType.URL:
                parsed = urlparse(self.url)
                if parsed.scheme in ['https', 'http']:
                    try:
                        with safe_urlopen(self.url) as r:
                            self.name = r.info().get_filename()
                    except (AttributeError, ValueError, URLError):
                        pass
                if not self.name:
                    # Fallback
                    self.name = os.path.basename(urlparse(self.url).path)
        # Handle `created_by` User
        user = get_current_user()
        if user and not user.pk:
            user = None
        if not self.pk:
            self.created_by = user
        # Must save the model with the file before accessing it for the checksum
        super(ChecksumFile, self).save(*args, **kwargs)

    def download_to_local_path(self, directory: str = None):
        """Forcibly download this file to a directory on disk.

        Cleanup must be handled by caller.

        This will handle locking to prevent multiple processes/threads
        from trying to download the file at the same time -- only one thread
        or process will perform the download and the rest will yield its
        result.

        """
        if directory is None:
            dest_path = self.get_cache_path()
        else:
            dest_path = Path(directory, self.name)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        # Thread/process safe locking for file access
        lock = get_file_lock(dest_path)

        with lock:  # TODO: handle timeouts in condition
            if dest_path.exists() and dest_path.stat().st_size > 0:
                # File already exists (is cached)
                logger.debug(f'Found cached file ({self.pk}) at: {dest_path}')
                # Touch the file so that it moves to the top of the priority list
                # when cleaning.
                dest_path.touch()
                return dest_path
            else:
                logger.debug(f'Downloading file ({self.pk}) to: {dest_path}')
                # If downloading to the cache, clean to achieve available free space
                if get_cache_dir() in dest_path.parents:
                    clean_file_cache()
                # TODO: handle if these fail (e.g. bad S3 credentials)
                if self.type == FileSourceType.FILE_FIELD:
                    return download_field_file_to_local_path(self.file, dest_path)
                elif self.type == FileSourceType.URL:
                    return download_url_file_to_local_path(self.url, dest_path)

    def get_cache_path(self):
        """Generate a predetermined path in the cache directory.

        This will use the associated FileSet's cache path if this resource
        has a file_set, otherwise it will place in the top of the cache
        directory.

        """
        if self.file_set is None:
            # If no file_set, place in the main cache directory
            directory = get_cache_dir() / f'f-{self.pk}'
            directory.mkdir(parents=True, exist_ok=True)
        else:
            directory = self.file_set.get_cache_path()
        return directory / f'{self.name}'

    @contextmanager
    def yield_local_path(self, try_fuse: bool = True, yield_file_set: bool = False):
        """Create a local path for this file and all other files in its file_set.

        This will first attempt to use httpfs to FUSE mount the file's URL if
        and only if the file does not belong to a FileSet. FUSE with multiple
        files in a FileSet is not yet supported.

        If FUSE is unavailable, this will fallback to downloading the entire
        file (and the other files in this item's FileSet) to local storage.

        Parameters
        ----------
        try_fuse : bool
            Try to use the FUSE interface. If false, use VSI or download to
            local storage.

        yield_file_set : bool
            Yield all of the files in this file's file_set if available.

        """
        # TODO: fix FUSE to handle adjacent files
        if (
            self.file_set is None
            and try_fuse
            and self.type == FileSourceType.URL
            and precheck_fuse(self.get_url())
        ):
            yield url_file_to_fuse_path(self.get_url(internal=True))
            return
        # Fallback to loading entire file locally - this uses `get_temp_path`
        logger.debug('`yield_local_path` falling back to downloading entire file to local storage.')
        path = self.get_cache_path()
        if yield_file_set and self.file_set:
            # NOTE: This is messy and should be improved but it ensures the directory remains locked
            with self.file_set.yield_all_to_local_path() as _:
                yield path
            return
        # Not in file_set. Download to cache dir
        from .utils import yield_checksumfiles

        with yield_checksumfiles([self], path.parent):
            yield path

    def get_url(self, internal: bool = False):
        """Get the URL of the stored resource.

        Parameters
        ----------
        internal : bool
            In most cases this URL will be accessible from anywhere. In some
            cases, this URL will only be accessible from within the container.
            This flag is for use with internal processes to make sure the host
            is correctly set to ``minio`` when needed. See
            ``patch_internal_presign`` for more details.

        """
        if self.type == FileSourceType.FILE_FIELD:
            if internal:
                with patch_internal_presign(self.file):
                    return self.file.url
            else:
                return self.file.url
        elif self.type == FileSourceType.URL:
            return self.url

    def data_link(self):
        return _link_url(self, 'get_url')

    data_link.allow_tags = True
