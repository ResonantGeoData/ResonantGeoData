import contextlib
import json
import logging
import os
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode, urlparse

from crum import get_current_user
from django.conf import settings
from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from filelock import FileLock
from model_utils.managers import InheritanceManager
from rgd.utility import (
    _link_url,
    clean_file_cache,
    compute_checksum_file_field,
    compute_checksum_url,
    compute_hash,
    download_field_file_to_local_path,
    download_url_file_to_local_path,
    get_cache_dir,
    patch_internal_presign,
    precheck_fuse,
    safe_urlopen,
    url_file_to_fuse_path,
    uuid_prefix_filename,
)
from s3_file_field import S3FileField

from .. import tasks
from .collection import Collection
from .constants import DB_SRID
from .mixins import PermissionPathMixin, TaskEventMixin

logger = logging.getLogger(__name__)


class SpatialEntry(models.Model):
    """Common model to all geospatial data entries.

    This is intended to be used in a mixin manner.

    """

    # `InheritanceManager` allows us to select inhereted tables via `objects.select_subclasses()`
    objects = InheritanceManager()

    spatial_id = models.AutoField(primary_key=True)

    # Datetime of creation for the dataset
    acquisition_date = models.DateTimeField(null=True, default=None, blank=True)

    # This can be used with GeoDjango's geographic database functions for spatial indexing
    footprint = models.GeometryField(srid=DB_SRID)
    outline = models.GeometryField(srid=DB_SRID)

    instrumentation = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='The instrumentation used to acquire these data.',
    )

    def __str__(self):
        try:
            return 'Spatial ID: {} (ID: {}, type: {})'.format(self.spatial_id, self.id, type(self))
        except AttributeError:
            return super().__str__()

    @property
    def bounds(self):
        extent = {
            'xmin': self.outline.extent[0],
            'ymin': self.outline.extent[1],
            'xmax': self.outline.extent[2],
            'ymax': self.outline.extent[3],
        }
        return extent

    @property
    def bounds_json(self):
        return json.dumps(self.bounds)


class FileSourceType(models.IntegerChoices):
    FILE_FIELD = 1, 'FileField'
    URL = 2, 'URL'


class ChecksumFile(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
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

    type = models.IntegerField(choices=FileSourceType.choices, default=FileSourceType.FILE_FIELD)
    file = S3FileField(null=True, blank=True, upload_to=uuid_prefix_filename)
    url = models.TextField(null=True, blank=True)

    task_funcs = (tasks.task_checksum_file_post_save,)
    permissions_paths = [('collection', Collection)]

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
            )
        ]

    @property
    def basename(self):
        return os.path.basename(self.name)

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

    def download_to_local_path(self, directory: str):
        """Forcibly download this file to a directory on disk.

        Cleanup must be handled by caller.

        This will handle locking to prevent multiple processes/threads
        from trying to download the file at the same time -- only one thread
        or process will perfrom the download and the rest will yield its
        result.

        """
        # Thread/process safe locking for file access
        dest_path = Path(directory, self.name)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        lock_file_path = f'{dest_path}.lock'
        lock = FileLock(
            lock_file_path
        )  # timeout=getattr(settings, 'RGD_FILE_LOCK_TIMEOUT', 10000))

        with lock:  # TODO: handle timeouts in condition
            if dest_path.exists() and dest_path.stat().st_size > 0:
                # File already exists (is cached)
                logger.info(f'Found cached file ({self.pk}) at: {dest_path}')
                # Touch the file so that it moves to the top of the priority list
                # when cleaning.
                dest_path.touch()
                return dest_path
            else:
                logger.info(f'Downloading file ({self.pk}) to: {dest_path}')
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

        This makes a directory under the cache directory for each ChecksumFile
        record. The subdirectory is the Primary Key of the record and the nested
        files are the file itself, lockfile, and any additional files used or
        generated by third party libraries.

        `<cache directory>/<pk>/*`

        """
        return os.path.join(get_cache_dir(), f'{self.pk}')

    def yield_local_path(self, vsi: bool = False, try_fuse: bool = True):
        """Create a local path for the file to be accessed.

        This will first attempt to use httpfs to FUSE mount the file's URL.
        If FUSE is unavailable, this will fallback to a Virtual File Systems
        URL (``vsicurl``) if the ``vsi`` option is set. Otherwise, this will
        download the entire file to local storage.

        Parameters
        ----------
        vsi : bool
            If FUSE fails, fallback to a Virtual File Systems URL. See
            ``get_vsi_path``. This is especially useful if the file
            is being utilized by GDAL and FUSE is not set up.
        try_fuse : bool
            Try to use the FUSE interface. If false, use VSI or download to
            local storage.

        """
        if try_fuse and self.type == FileSourceType.URL and precheck_fuse(self.get_url()):
            return url_file_to_fuse_path(self.get_url(internal=True))
        elif vsi and self.type != FileSourceType.FILE_FIELD:
            logger.info('`yield_local_path` falling back to Virtual File System URL.')
            return self.yield_vsi_path(internal=True)
        # Fallback to loading entire file locally - this uses `get_temp_path`
        logger.info('`yield_local_path` falling back to downloading entire file to local storage.')
        return self.download_to_local_path(self.get_cache_path())

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

    def get_vsi_path(self, internal: bool = False) -> str:
        """Return the GDAL Virtual File Systems [0] URL.

        This currently formulates the `/vsicurl/...` URL [1] for internal and
        external files. This is assuming that both are read-only. External
        files can still be from private S3 buckets as long as `self.url`
        redirects to a presigned S3 URL [1]:

            > Starting with GDAL 2.1, `/vsicurl/` will try to query directly
              redirected URLs to Amazon S3 signed URLs during their validity
              period, so as to minimize round-trips.

        This URL can be used for both GDAL and Rasterio [2]:

            > To help developers switch [from GDAL], Rasterio will accept
              [vsi] identifiers and other format-specific connection
              strings, too, and dispatch them to the proper format drivers
              and protocols.

        `/vsis3/` could be used for...
            * read/write access
            * directory listing (for sibling files)
        ...but is a bit more of a challenge to setup. [2]

        [0] https://gdal.org/user/virtual_file_systems.html
        [1] https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access
        [2] https://gdal.org/user/virtual_file_systems.html#vsis3-aws-s3-files
        [3] https://rasterio.readthedocs.io/en/latest/topics/switch.html?highlight=vsis3#dataset-identifiers

        """
        url = self.get_url(internal=internal)
        if url.startswith('s3://'):
            s3_path = url.replace('s3://', '')
            vsi = f'/vsis3/{s3_path}'
        else:
            gdal_options = {
                'url': url,
                'use_head': 'no',
                'list_dir': 'no',
            }
            vsi = f'/vsicurl?{urlencode(gdal_options)}'
        logger.info(f'vsi URL: {vsi}')
        return vsi

    @contextlib.contextmanager
    def yield_vsi_path(self, internal: bool = False):
        """Wrap ``get_vsi_path`` in a context manager."""
        yield self.get_vsi_path(internal=internal)


class WhitelistedEmail(models.Model):
    """Pre-approve users for sign up by their email."""

    email = models.EmailField()


class SpatialAsset(SpatialEntry, TimeStampedModel, PermissionPathMixin):
    """Any spatially referenced file set.

    This can be any collection of files that have a spatial reference and are
    not explicitly handled by the other SpatialEntry subtypes. For example, this
    model can be used to hold a collection of PDF documents or slide decks that
    have a georeference.

    """

    permissions_paths = [('files', ChecksumFile)]

    files = models.ManyToManyField(ChecksumFile, related_name='+')
