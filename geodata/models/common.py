import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.utils import timezone


class DeferredFieldsManager(models.Manager):
    def __init__(self, *deferred_fields):
        self.deferred_fields = deferred_fields
        super().__init__()

    def get_queryset(self):
        return super().get_queryset().defer(*self.deferred_fields)


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
    acquisition_date = models.DateTimeField(null=True, default=None)

    class Meta:
        abstract = True

    def __str__(self):
        return '{} {} (type: {})'.format(self.id, self.name, type(self))


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
