import traceback

from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def _safe_execution(func, *args, **kwargs):
    """Execute a task and return any tracebacks that occur as a string."""
    try:
        func(*args, **kwargs)
        return ''
    except Exception as exc:
        logger.exception(f'Internal error run `{func.__name__}`: {exc}')
        return traceback.format_exc()


def _run_with_failure_reason(model, func, *args, **kwargs):
    """Run a function that will update the model's `failure_reason`."""
    from rgd.models.mixins import Status

    model.status = Status.RUNNING
    model.save(update_fields=['status'])
    model.failure_reason = _safe_execution(func, *args, **kwargs)
    if model.failure_reason:
        model.status = Status.FAILED
    else:
        model.status = Status.SUCCEEDED
    model.save(update_fields=['failure_reason', 'status'])
