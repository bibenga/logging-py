import logging
import logging.config
from typing import Any

from celery import Task, signals, states


def setup_celery_logging(setup_logging: bool = True) -> None:
    if setup_logging:
        signals.setup_logging.connect(on_setup_logging, weak=False)
    signals.task_prerun.connect(on_task_prerun, weak=False)
    signals.task_postrun.connect(on_task_postrun, weak=False)


def on_setup_logging(**kwargs):
    try:
        from django.conf import settings
        logging.config.dictConfig(settings.LOGGING)
    except ImportError:
        pass


logger = logging.getLogger(__name__)


def on_task_prerun(task_id: Any, task: Task, **kwargs):
    logger.info(
        "Task %r started", task_id,
        extra={
            "extra": {
                "labels.celery_task_id": str(task_id),
                "labels.celery_task_name": task.name,
            },
        },
    )


def on_task_postrun(task_id: Any, task: Task, **kwargs):
    state = kwargs.get("state")
    if state in states.EXCEPTION_STATES:
        level = logging.ERROR
        exc_info = True
    else:
        level = logging.INFO
        exc_info = False
    logger.log(
        level,
        "Task %r finished with state %s", task_id, state,
        exc_info=exc_info,
        extra={
            "extra": {
                "labels.celery_task_id": str(task_id),
                "labels.celery_task_name": task.name,
                "labels.celery_task_state": state,
            },
        },
    )
