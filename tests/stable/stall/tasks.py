import logging
from celery import shared_task


log = logging.getLogger(__name__)


# from tests.stable.stall.tasks import send_email
# send_email.delay()

@shared_task
def send_email(**params) -> dict:
    log.info("send_email: %s", params)
    return params