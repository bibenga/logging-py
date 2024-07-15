import logging
from celery import shared_task


log = logging.getLogger(__name__)


# from tests.stable.stall.tasks import send_email, send_money
# send_email.delay()
# send_money.delay()

@shared_task
def send_email(**params) -> dict:
    log.info("send_email: %s", params)
    return params

@shared_task
def send_money(**params) -> None:
    _ = 1 / 0
