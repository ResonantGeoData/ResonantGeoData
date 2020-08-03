# from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils import timezone
from model_utils.managers import InheritanceManager

from rgd.utility import _field_file_to_local_path, compute_checksum
from .constants import DB_SRID


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
        super(ModifiableEntry, self).save(*args, **kwargs)


class SpatialEntry(models.Model):
    """Common model to all geospatial data entries.

    This is intended to be used in a mixin manner.

    """

    spatial_id = models.AutoField(primary_key=True)

    # Datetime of creation for the dataset
    acquisition_date = models.DateTimeField(null=True, default=None, blank=True)

    # This can be used with GeoDjango's geographic database functions for spatial indexing
    footprint = models.PolygonField(srid=DB_SRID, null=True, blank=True)
    outline = models.PolygonField(srid=DB_SRID, null=True, blank=True)

    objects = InheritanceManager()

    def __str__(self):
        return 'Spatial ID, name: {}, {} (type: {})'.format(self.spatial_id, self.name, type(self))


class ChecksumFile(ModifiableEntry):
    """A base class for tracking files.

    Child class must implement a file field called ``file``! This ensures the
    field is initialized with coorect options like uplaod location and
    validators.

    """

    name = models.CharField(max_length=100, blank=True, null=True)
    checksum = models.CharField(max_length=64, blank=True, null=True)
    compute_checksum = models.BooleanField(
        default=False
    )  # a flag to recompute the checksum on save
    validate_checksum = models.BooleanField(
        default=False
    )  # a flag to validate the checksum against the saved checksum
    last_validation = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # TODO: is there a cleaner way to enforce child class has `file` field?
        if not hasattr(self, 'file'):
            raise AttributeError('Child class of `ChecksumFile` must have a `file` field.')
        if not self.name:
            self.name = self.file.name
        # Must save the model with the file before accessing it for the checksum
        super(ChecksumFile, self).save(*args, **kwargs)
        # Checksum is additional step after saving everything else - simply update these fields.
        if self.compute_checksum or self.validate_checksum:
            previous = self.checksum
            with _field_file_to_local_path(self.file) as file_path:
                self.checksum = compute_checksum(file_path)
            if self.validate_checksum:
                self.last_validation = self.checksum == previous
            # Reset the user flags
            self.compute_checksum = False
            self.validate_checksum = False
            # Simple update save - not full save
            super(ChecksumFile, self).save(
                update_fields=[
                    'checksum',
                    'compute_checksum',
                    'last_validation',
                    'validate_checksum',
                ]
            )
        return
