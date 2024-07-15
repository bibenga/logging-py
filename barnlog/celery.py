from typing import Any

from barnlog.logging import logging_config
from barnlog.utils import Local

_celery_task_info = Local()


def get_celery_task_info() -> dict[str, Any] | None:
    return getattr(_celery_task_info, "value", None)


def setup_celery_logging(setup_logging: bool = True) -> None:
    from celery import Task, signals
    if setup_logging:
        signals.setup_logging.connect(on_setup_logging, weak=False)
    signals.task_prerun.connect(on_task_prerun, weak=False)
    signals.task_postrun.connect(on_task_postrun, weak=False)


def on_setup_logging(**kwargs):
    try:
        from django.conf import settings
        logging_config(settings.LOGGING)
    except ImportError:
        pass


def on_task_prerun(task_id: Any, task: Any, **kwargs):
    _celery_task_info.value = {
        "id": task_id,
        "name": task.name,
    }


def on_task_postrun(**kwargs):
    if hasattr(_celery_task_info, "value"):
        del _celery_task_info.value
