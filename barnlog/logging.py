import logging
import logging.config
import logging.handlers
import platform
import queue
import sys
import threading

import requests


def logging_config(value: dict) -> None:
    logging.setLogRecordFactory(ExtraLogRecord)
    logging.config.dictConfig(value)


class ExtraLogRecord(logging.LogRecord):
    def __init__(self, name, level, pathname, lineno, msg, args, exc_info, func, sinfo):
        super().__init__(name, level, pathname, lineno, msg, args, exc_info, func, sinfo)

        from barnlog.celery import get_celery_task_info
        from barnlog.django import get_django_user_info, get_django_request_info

        self.user = get_django_user_info()
        self.http = get_django_request_info()
        self.celery = get_celery_task_info()


class HttpHandler(logging.Handler):
    console = logging.getLogger("console")

    def __init__(
        self,
        *args,
        app_name: str = "backend",
        url: str = "http://localhost:2021/log/ingest",
        timeout: int = 5,
        sync: bool = True,
        queue_size: int = 100,
        **kwargs
    ) -> None:
        super().__init__(*args, **kwargs)

        self._app_name = app_name
        self._hostname = platform.node()
        self._python = sys.version

        self._session = requests.Session()
        self._url = url
        self._timeout = timeout

        self._sync = sync
        if not self._sync:
            self._log_queue = queue.Queue(maxsize=queue_size)
            self._thread = threading.Thread(target=self._process, name="log-processor", daemon=True)
            self._thread.start()

    def mapLogRecord(self, record: logging.LogRecord):
        exc_text = record.exc_text
        if record.exc_info and not record.exc_text:
            exc_text = self.formatter.formatException(record.exc_info)
        stack_info = None
        if record.stack_info:
            stack_info = self.formatter.formatStack(record.stack_info)

        t = self.formatter.formatTime(record, "%Y-%m-%dT%H:%M:%S")
        t = "%s.%03dZ" % (t, record.msecs)

        res = {
            "@timestamp": t,
            "level": record.levelname,
            "name": record.name,
            "message": record.message,

            "app": self._app_name,
            "hostname": self._hostname,
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
            "python": self._python,
        }

        if hasattr(record, "user") and record.user:
            res["user"] = record.user

        if hasattr(record, "http") and record.http:
            res["http"] = record.http

        if hasattr(record, "celery") and record.celery:
            res["celery"] = record.celery

        if hasattr(record, "extra") and record.extra:
            res["extra"] = record.extra

        return res

    def emit(self, record):
        if self._sync:
            self._post([self.mapLogRecord(record)])
        else:
            try:
                data = self.mapLogRecord(record)
                self._log_queue.put(data, True, 0.5)
            except queue.Full:
                self.handleError(record)

    def close(self) -> None:
        if not self._sync:
            self._log_queue.put(None, True)
            try:
                self._thread.join(10)
            except:
                self.console.fatal("HttpHandler - failed during stop", exc_info=True)
        return super().close()

    def _process(self):
        # if we enable this logging then we receive some strange deadlock
        self.console.info("HttpHandler - queue processor started")
        while True:
            try:
                obj = self._log_queue.get(True, 1)
            except queue.Empty:
                continue

            if obj is None:
                break

            self._post([obj])
        self.console.info("HttpHandler - queue processor terminated")

    def _post(self, data) -> None:
        try:
            response = self._session.post(self._url, json=data, timeout=self._timeout)
            response.raise_for_status()
        except:
            self.console.fatal("can't send request", exc_info=True)


class QueueHandler(logging.handlers.QueueHandler):
    def enqueue(self, record: logging.LogRecord) -> None:
        self.queue.put(record)


class QueueListener(logging.handlers.QueueListener):
    def start(self) -> None:
        if not self._thread or not self._thread.is_alive():
            return super().start()
