from contextlib import contextmanager
import logging
import os
from urllib.parse import urlencode, urlparse

# from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from girder_utils.files import field_file_to_local_path
from model_utils.managers import InheritanceManager
from s3_file_field import S3FileField

from rgd.utility import (
    _link_url,
    compute_checksum_file,
    compute_checksum_url,
    patch_internal_presign,
    precheck_fuse,
    url_file_to_fuse_path,
    url_file_to_local_path,
)

from .. import tasks
from .collection import Collection
from .constants import DB_SRID
from .mixins import Status, TaskEventMixin

logger = logging.getLogger(__name__)


class ModifiableEntry(models.Model):
    """A base class for models that need to track modified datetimes and users."""

    modified = models.DateTimeField(editable=False, help_text='The last time this entry was saved.')
    created = models.DateTimeField(editable=False, help_text='When this was added to the database.')
    # creator = models.ForeignKey(
    #     get_user_model(), on_delete=models.DO_NOTHING, related_name='creator'
    # )
    # modifier = models.ForeignKey(
    #     get_user_model(), on_delete=models.DO_NOTHING, related_name='modifier'
    # )

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        if 'update_fields' in kwargs:
            kwargs = kwargs.copy()
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'modified'}
        super(ModifiableEntry, self).save(*args, **kwargs)


class SpatialEntry(models.Model):
    """Common model to all geospatial data entries.

    This is intended to be used in a mixin manner.

    """

    spatial_id = models.AutoField(primary_key=True)

    # Datetime of creation for the dataset
    acquisition_date = models.DateTimeField(null=True, default=None, blank=True)

    # This can be used with GeoDjango's geographic database functions for spatial indexing
    footprint = models.PolygonField(srid=DB_SRID)
    outline = models.PolygonField(srid=DB_SRID)

    objects = InheritanceManager()

    def __str__(self):
        return 'Spatial ID: {} (ID: {}, type: {})'.format(self.spatial_id, self.id, type(self))

    @property
    def subentry(self):
        try:
            return self.rastermetaentry
        except ObjectDoesNotExist:
            pass
        try:
            return self.geometryentry
        except ObjectDoesNotExist:
            pass
        try:
            return self.fmventry
        except ObjectDoesNotExist:
            pass
        raise ObjectDoesNotExist

    @property
    def subentry_name(self):
        """Return the name from the subentry model."""
        return self.subentry.name

    @property
    def subentry_type(self):
        return type(self.subentry).__name__


class FileSourceType(models.IntegerChoices):
    FILE_FIELD = 1, 'FileField'
    URL = 2, 'URL'


class ChecksumFile(ModifiableEntry, TaskEventMixin):
    """The main class for user-uploaded files.

    This has support for manually uploading files or specifing a URL to a file
    (for example in an existing S3 bucket).

    """

    name = models.CharField(max_length=100, blank=True)
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

    type = models.IntegerField(choices=FileSourceType.choices, default=FileSourceType.FILE_FIELD)
    file = S3FileField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)

    task_funcs = (tasks.task_checksum_file_post_save,)
    failure_reason = models.TextField(null=True)
    status = models.CharField(max_length=20, default=Status.CREATED, choices=Status.choices)

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

    def __str__(self):
        return self.name

    def get_checksum(self):
        """Compute a new checksum without saving it."""
        if self.type == FileSourceType.FILE_FIELD:
            return compute_checksum_file(self.file)
        elif self.type == FileSourceType.URL:
            return compute_checksum_url(self.url)
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

    def save(self, *args, **kwargs):
        if not self.name:
            if self.type == FileSourceType.FILE_FIELD and self.file.name:
                self.name = os.path.basename(self.file.name)
            elif self.type == FileSourceType.URL:
                # TODO: this isn't the best approach
                self.name = os.path.basename(urlparse(self.url).path)
        # Must save the model with the file before accessing it for the checksum
        super(ChecksumFile, self).save(*args, **kwargs)

    def yield_local_path(self, vsi=False):
        """Create a local path for the file to be accessed.

        This will first attempt to use httpfs to FUSE mount the file's URL.
        If FUSE is unavailable, this will fallback to a Virtual File Systems URL (``vsicurl``) if the ``vsi`` option is set. Otherwise, this will
        download the entire file to local storage.

        Parameters
        ----------
        vsi : bool
            If FUSE fails, fallback to a Virtual File Systems URL. See
            ``get_local_vsi_path``. This is especially useful if the file
            is being utilized by GDAL and FUSE is not set up.

        """
        if precheck_fuse(self.get_url()):
            return url_file_to_fuse_path(self.get_url())
        else:
            if vsi:
                logger.info('`yield_local_path` falling back to Virtual File System URL.')
                return self.yield_local_vsi_path()
            # Fallback to loading entire file locally
            logger.info(
                '`yield_local_path` falling back to downloading entire file to local storage.'
            )
            if self.type == FileSourceType.FILE_FIELD:
                return field_file_to_local_path(self.file)
            elif self.type == FileSourceType.URL:
                return url_file_to_local_path(self.url)

    def get_url(self):
        """Get the URL of the stored resource."""
        if self.type == FileSourceType.FILE_FIELD:
            return self.file.url
        elif self.type == FileSourceType.URL:
            return self.url

    def data_link(self):
        return _link_url('geodata', 'image_file', self, 'get_url')

    data_link.allow_tags = True

    def get_local_vsi_path(self) -> str:
        """Return the GDAL Virtual File Systems [0] URL.

        In most cases this URL will be accessible from anywhere. In some cases,
        this URL will only be accessible from within the container. See
        `patch_internal_presign` for more details.

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
        with patch_internal_presign(self.file):
            url = self.get_url()
        gdal_options = {
            'url': url,
            'use_head': 'no',
            'list_dir': 'no',
        }
        vsicurl = f'/vsicurl?{urlencode(gdal_options)}'
        logger.info(f'vsicurl URL: {vsicurl}')
        return vsicurl

    @contextmanager
    def yield_local_vsi_path(self):
        """Wrap ``get_local_vsi_path`` in a context manager."""
        yield self.get_local_vsi_path()
