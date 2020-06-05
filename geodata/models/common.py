import tempfile

from django.conf import settings
from django.contrib.gis.db import models
from django.utils import timezone


class DeferredFieldsManager(models.Manager):
    def __init__(self, *deferred_fields):
        self.deferred_fields = deferred_fields
        super().__init__()

    def get_queryset(self):
        return super().get_queryset().defer(*self.deferred_fields)


class ModifiableEntry(models.Model):
    """A base class for models that need to track modified datetimes."""

    modified = models.DateTimeField(editable=False, help_text='The last time this entry was saved.')
    created = models.DateTimeField(editable=False, help_text='When this was added to the database.')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        super(ModifiableEntry, self).save(*args, **kwargs)


class PostSaveEventModel(models.Model):
    """A base class for models that must call a post-save task.

    The task must be assigned as a class attribute.

    NOTE: you still need to register the post save event.
    """

    task_name = None
    """A string name of the task in the `tasks` module. Use string to avoid
    recursive imports."""

    def _run_post_save_task(self):
        """Validate the raster asynchronously."""
        if not isinstance(self.task_name, str):
            raise RuntimeError('Task name must be set!')
        from .. import tasks

        task = getattr(tasks, self.task_name)
        task.delay(self.id)

    def _post_save(self, created, *args, **kwargs):
        if (
            not created
            and kwargs.get('update_fields')
            and 'data' not in kwargs.get('update_fields')
        ):
            return
        self._run_post_save_task()


class SpatialEntry(ModifiableEntry):
    """Common model to all geospatial data entries."""

    name = models.CharField(max_length=100, blank=True, null=True)
    # An optional description field in case the user needs to add context
    description = models.TextField(blank=True, null=True)
    # Datetime of creation for the dataset
    acquisition_date = models.DateTimeField(default=timezone.now)

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
