"""Mixin helper classes."""


class TaskEventMixin(object):
    """A mixin for models that must call a task.

    The task must be assigned as a class attribute.

    NOTE: you still need to register the pre/post save event.  on_commit events
    should be registered as post_save events, not pre_save.
    """

    task_func = None
    """The task function."""

    def _run_task(self):
        """Validate the raster asynchronously."""
        if not callable(self.task_func):
            raise RuntimeError('Task function must be set to a callable.')
        self.task_func.delay(self.id)

    def _post_save_event_task(self, created, *args, **kwargs):
        if not created and kwargs.get('update_fields'):
            return
        self._run_task()

    def _on_commit_event_task(self, *args, **kwargs):
        if kwargs.get('update_fields'):
            return
        self._run_task()
