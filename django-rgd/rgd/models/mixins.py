"""Mixin helper classes."""
import logging
from typing import Iterable

from celery import Task
from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class Status(models.TextChoices):
    CREATED = 'created', _('Created but not queued')
    QUEUED = 'queued', _('Queued for processing')
    RUNNING = 'running', _('Processing')
    FAILED = 'failed', _('Failed')
    SUCCEEDED = 'success', _('Succeeded')


class TaskEventMixin(models.Model):
    """A mixin for models that must call a set of celery tasks.

    This mixin adds three class attributes:

    * ``task_funcs``, which should be the list of celery task functions that should be run
      on this model instance. Subclasses should set this attribute.
    * ``status``, a model field representing task execution status.
    * ``failure_reason``, a model field that can be set on this instance from within
      tasks for human-readable error logging.

    NOTE: you still need to register the pre/post save event.  on_commit events
    should be registered as post_save events, not pre_save.
    """

    class Meta:
        abstract = True

    failure_reason = models.TextField(null=True)
    status = models.CharField(max_length=20, default=Status.CREATED, choices=Status.choices)

    task_funcs: Iterable[Task] = []

    def _run_tasks(self) -> None:
        logger.info(f'in task callback for {self}')
        if not self.task_funcs:
            return

        self.status = Status.QUEUED
        self.save(
            update_fields=[
                'status',
            ]
        )
        for func in self.task_funcs:
            func.delay(self.id)

    def _post_save_event_task(self, created: bool, *args, **kwargs) -> None:
        if not created and kwargs.get('update_fields'):
            return
        self._run_tasks()

    def _on_commit_event_task(self, *args, **kwargs) -> None:
        if kwargs.get('update_fields'):
            return
        self._run_tasks()
