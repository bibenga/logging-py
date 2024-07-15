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


def get_app_name() -> str:
    return os.getenv("APP_NAME", "barnlog")


def get_version() -> str:
    return os.getenv("APP_VERSION", "0.0.0")


@cache
def get_hostname() -> str:
    return platform.node()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        super().format(record)
        return json.dumps(self.serialize(record), ensure_ascii=False, sort_keys=True)

    def serialize(self, record: logging.LogRecord) -> dict:
        t = self.formatTime(record, "%Y-%m-%dT%H:%M:%S")
        t = "%s.%03dZ" % (t, record.msecs)

        app_name = get_app_name()
        app_version = get_version()
        python_version = sys.version
        hostname = get_hostname()

        res = {
            "@timestamp": t,
            "ecs.version": "1.2.0",

            "tags": [tag for tag in [app_name] if tag],

            "log.logger": record.name,
            "log.level": record.levelname,
            "log.origin.file.name": record.pathname,
            "log.origin.function": record.funcName,
            "log.origin.file.line": record.lineno,

            "message": record.message,

            "process.pid": record.process,
            "process.name": record.processName,
            "process.uptime": record.relativeCreated / 1000,
            "process.thread.id": record.thread,
            "process.thread.name": f"{record.threadName}:{record.taskName}" if record.taskName else record.threadName,

            # labels is a flat dict[str, str]
            "labels.hostname": hostname,
            "labels.python_version": python_version,
            "labels.app_name": app_name,
            "labels.app_version": app_version,
        }

        if record.exc_info:
            exc_text = record.exc_text
            if not record.exc_text:
                exc_text = self.formatException(record.exc_info)

            stack_info = None
            if record.stack_info:
                stack_info = self.formatStack(record.stack_info)

            res["error.message"] = exc_text
            res["error.stack_trace"] = stack_info
            if record.exc_info and record.exc_info[0]:
                error_cls = record.exc_info[0]
                res["error.type"] = f"{error_cls.__module__}.{error_cls.__name__}"

        if hasattr(record, "extra") and record.extra:
            for key, value in record.extra.items():
                if value is None or isinstance(value, str):
                    pass
                elif isinstance(value, (bool, int, float)):
                    if key.startswith("labels."):
                        value = str(value)
                else:
                    value = str(value)
                res[key] = value

        return res


class UnflatJsonFormatter(JsonFormatter):
    def serialize(self, record: logging.LogRecord) -> dict:
        return self.unflat(super().serialize(record))

    def unflat(self, value: dict[str, Any]) -> dict:
        res = {}
        for key, value in value.items():
            if "." in key:
                subkeys = key.split(".")
                obj = res
                for pos, subkey in enumerate(subkeys):
                    if pos == len(subkeys) - 1:
                        break
                    if subkey in obj:
                        obj = obj[subkey]
                    else:
                        obj[subkey] = {}
                        obj = obj[subkey]
                obj[subkeys[-1]] = value
            else:
                res[key] = value
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
