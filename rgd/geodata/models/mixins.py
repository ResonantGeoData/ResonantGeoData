"""Mixin helper classes."""
from collections.abc import Iterable

from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _


class Status(models.TextChoices):
    CREATED = 'created', _('Created but not queued')
    QUEUED = 'queued', _('Queued for processing')
    RUNNING = 'running', _('Processing')
    FAILED = 'failed', _('Failed')
    SUCCEEDED = 'success', _('Succeeded')


class TaskEventMixin(object):
    """A mixin for models that must call a task.

    The task must be assigned as a class attribute.

    NOTE: you still need to register the pre/post save event.  on_commit events
    should be registered as post_save events, not pre_save.
    """

    task_funcs = None
    """The task function."""

    def _run_task(self):
        if not isinstance(self.task_funcs, Iterable):
            self.task_funcs = (self.task_funcs,)
        if not all([callable(f) for f in self.task_funcs]):
            raise RuntimeError('Task function(s) must be set to a callable.')  # pragma: no cover
        self.status = Status.QUEUED
        self.save(
            update_fields=[
                'status',
            ]
        )
        for func in self.task_funcs:
            func.delay(self.id)

    def _post_save_event_task(self, created, *args, **kwargs):
        if not created and kwargs.get('update_fields'):
            return
        self._run_task()

    def _on_commit_event_task(self, *args, **kwargs):
        if kwargs.get('update_fields'):
            return
        self._run_task()
