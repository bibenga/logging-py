from celery import Celery

from barnlog.celery import setup_celery_logging

setup_celery_logging()
app = Celery()
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
