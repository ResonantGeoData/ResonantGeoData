"""Mixin helper classes."""


class PostSaveEventModel(object):
    """A base class for models that must call a post-save task.

    The task must be assigned as a class attribute.

    NOTE: you still need to register the post save event.
    """

    task_func = None
    """The task function."""

    def _run_post_save_task(self):
        """Validate the raster asynchronously."""
        if not callable(self.task_func):
            raise RuntimeError('Task function must be set to a callable.')
        self.task_func.delay(self.id)

    def _post_save(self, created, *args, **kwargs):
        if (
            not created
            and kwargs.get('update_fields')
            and 'data' not in kwargs.get('update_fields')
        ):
            return
        self._run_post_save_task()
