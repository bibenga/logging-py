import base64
import json
import logging
import logging.config
import logging.handlers
import os
import platform
import sys
from functools import cache
from typing import Any


def logging_config(value: dict) -> None:
    logging.setLogRecordFactory(ExtraLogRecord)
    logging.config.dictConfig(value)


@cache
def get_app_name() -> str:
    return os.getenv("APP_NAME") or "barnlog"


@cache
def get_version() -> str:
    return os.getenv("APP_VERSION") or "0.0.0"


@cache
def get_hostname() -> str:
    return platform.node()


class ExtraLogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        from barnlog.celery import get_celery_task_info
        from barnlog.django import get_django_request_info, get_django_user_info

        self.app_name = get_app_name()
        self.app_version = get_version()
        # self.python_version = sys.version
        self.hostname = get_hostname()

        self.user = get_django_user_info()
        self.http_server = get_django_request_info()
        self.celery = get_celery_task_info()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        super().format(record)
        return json.dumps(self.serialize(record), ensure_ascii=True)

    def serialize(self, record: logging.LogRecord) -> dict:
        exc_text = record.exc_text
        if record.exc_info and not record.exc_text:
            exc_text = self.formatException(record.exc_info)

        stack_info = None
        if record.stack_info:
            stack_info = self.formatStack(record.stack_info)

        t = self.formatTime(record, "%Y-%m-%dT%H:%M:%S")
        t = "%s.%03dZ" % (t, record.msecs)

        res = {
            "@timestamp": t,
            "level": record.levelname,
            "name": record.name,
            "message": record.message,

            "app_name": getattr(record, "app_name", None),
            "version": getattr(record, "app_version", None),
            # "python":  getattr(record, "python_version", None),
            "hostname": getattr(record, "hostname", None),
            "process": {
                "id": record.process,
                "name": record.processName,
            },
            "thread": {
                "id": record.thread,
                "name": record.threadName,
            },
            "task": {  # asyncio
                "name": record.taskName,
            },
            "pathname": record.pathname,
            "module": record.module,
            "filename": record.filename,
            "func_name": record.funcName,
            "exc_text": exc_text,
            "stack_info": stack_info,
        }

        if hasattr(record, "user") and record.user:
            res["user"] = record.user

        # if hasattr(record, "http_server") and record.http_server:
        #     res["http_server"] = record.http_server
        # if hasattr(record, "celery") and record.celery:
        #     res["celery"] = record.celery
        # if hasattr(record, "extra") and record.extra:
        #     res["extra"] = record.extra

        extra = getattr(record, "extra", None) or {}
        if hasattr(record, "http_server") and record.http_server:
            extra["http_server"] = record.http_server
        if hasattr(record, "celery") and record.celery:
            extra["celery"] = record.celery
        if extra:
            res["extra"] = extra

        return res


class HTTPHandler(logging.handlers.HTTPHandler):
    def __init__(self, host, url, secure=False, credentials=None, context=None,
                 token=None, timeout=None):
        super().__init__(host, url, method="POST", secure=secure, credentials=credentials,
                         context=context)
        self.token = token
        self.timeout = float(timeout) if timeout else 1
        if self.credentials and self.token:
            raise ValueError("credentials or token, not both")

    def emit(self, record):
        try:
            data = self.format(record).encode('utf-8')
            h = self.getConnection(self.host, self.secure)
            h.timeout = self.timeout
            h.putrequest(self.method, self.url)
            h.putheader("Content-Type", "application/json")
            h.putheader("Content-length", str(len(data)))
            if self.token:
                s = f'Token {self.token}'
                h.putheader('Authorization', s)
            elif self.credentials:
                s = ('%s:%s' % self.credentials).encode('utf-8')
                s = 'Basic ' + base64.b64encode(s).strip().decode('ascii')
                h.putheader('Authorization', s)
            h.endheaders()
            h.send(data)
            r = h.getresponse()
            if not (200 <= r.status < 300):
                raise RuntimeError(f"response status is bad")
        except Exception:
            self.handleError(record)


class QueueHandler(logging.handlers.QueueHandler):
    def enqueue(self, record: logging.LogRecord) -> None:
        self.queue.put(record)

    def prepare(self, record: logging.LogRecord) -> Any:
        return self.format(record)


class QueueListener(logging.handlers.QueueListener):
    def start(self) -> None:
        if not self._thread or not self._thread.is_alive():
            return super().start()
