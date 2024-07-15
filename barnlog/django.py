import logging
import logging.config
import os
import platform
import threading
import time
from typing import Any

from barnlog.utils import Local


def get_django_user_info() -> dict[str, Any] | None:
    # return getattr(_django_http_request_context, "value", None)
    if hasattr(_django_request, "value"):
        request = _django_request.value
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            return {
                "id": user.id,
                "username": user.username if user.username else None,
                "is_authenticated": user.is_authenticated,
            }
        return {
            "id": None,
            "username": "",
            "is_authenticated": False,
        }


# django request handler logging context
_django_request = Local()


def get_django_request():
    if hasattr(_django_request, "value"):
        return _django_request.value


def get_django_request_info() -> dict[str, Any] | None:
    if hasattr(_django_request, "value"):
        request = _django_request.value
        return {
            "request_id": getattr(request, "request_id", None),
            "method": request.method,
            "path": request.path,
        }


def request_id_middleware(get_response):
    # One-time configuration and initialization.
    from django.conf import settings
    # from django.utils.crypto import get_random_string

    REQUEST_ID_HEADER = getattr(settings, "REQUEST_ID_HEADER", "HTTP_X_REQUEST_ID")

    hostname = platform.node()
    # prefix = get_random_string(8)
    prefix = str(os.getpid())
    counter = 0
    lock = threading.Lock()

    def get_new_request_id() -> str:
        nonlocal counter
        with lock:
            counter += 1
            value = counter
        return f"{hostname}-{prefix}-{value:0>8}"

    def get_request_id(request) -> str:
        if hasattr(request, "request_id"):
            return request.request_id
        elif REQUEST_ID_HEADER:
            return request.META.get(REQUEST_ID_HEADER, "") or get_new_request_id()
        else:
            return get_new_request_id()

    def middleware(request):
        request_id = get_request_id(request)
        request.request_id = request_id
        _django_request.value = request
        try:
            response = get_response(request)
        finally:
            if hasattr(_django_request, "value"):
                del _django_request.value

        return response

    return middleware


def access_log_middleware(get_response):
    from django.conf import settings

    access = logging.getLogger(getattr(settings, "REQUEST_LOGGER_NAME", "access"))

    def middleware(request):
        request_id = getattr(request, "request_id", None)
        access.info("Start request %s: %s %s", request_id, request.method, request.path)
        start = time.time()
        try:
            response = get_response(request)
        except Exception as e:
            duration = time.time() - start
            access.error("Failed request %s: duration=%.4f, error=%s",
                         request_id, duration, str(e), exc_info=True)
            raise
        else:
            duration = time.time() - start
            access.info("Processed request %s: duration=%.4f, status_code=%s",
                        request_id, duration, response.status_code)
        return response

    return middleware
