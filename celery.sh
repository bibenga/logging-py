#!/bin/sh

# celery -A  tests.stable worker -E -P solo -l debug -B --scheduler django_celery_beat.schedulers:DatabaseScheduler
celery -A tests.stable worker -E -P solo -l info -B
