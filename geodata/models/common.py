import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils import timezone

from rgd.utility import _field_file_to_local_path, compute_checksum


class ModifiableEntry(models.Model):
    """A base class for models that need to track modified datetimes and users."""

    modified = models.DateTimeField(editable=False, help_text='The last time this entry was saved.')
    created = models.DateTimeField(editable=False, help_text='When this was added to the database.')
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.DO_NOTHING, related_name='creator'
    )
    modifier = models.ForeignKey(
        get_user_model(), on_delete=models.DO_NOTHING, related_name='modifier'
    )

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        super(ModifiableEntry, self).save(*args, **kwargs)


class SpatialEntry(ModifiableEntry):
    """Common model to all geospatial data entries."""

    name = models.CharField(max_length=100, blank=True, null=True)
    # An optional description field in case the user needs to add context
    description = models.TextField(blank=True, null=True)
    # Datetime of creation for the dataset
    acquisition_date = models.DateTimeField(null=True, default=None, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return '{} {} (type: {})'.format(self.id, self.name, type(self))


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
    last_validation = models.BooleanField(default=False)

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


class _ReaderRoutine(object):
    """A base class for defining reader routines.

    Subclasses will parse file(s) and generate new model entries.

    """

    def __init__(self, model_id):
        self.model_id = model_id

        # TODO: add a setting like this:
        workdir = getattr(settings, 'GEODATA_WORKDIR', None)
        self.tmpdir = tempfile.mkdtemp(dir=workdir)

    def _read_files(self):
        """Must return True for success."""
        raise NotImplementedError()

    def _save_entries(self):
        raise NotImplementedError()

    def run(self):
        if self._read_files():
            # Only attempt save if the read was successful
            self._save_entries()
