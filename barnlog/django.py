import logging
import logging.config
import os
import platform
import threading
import time

logger = logging.getLogger(__name__)


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
        return get_response(request)

    return middleware


def access_log_middleware(get_response):
    def middleware(request):
        request_id = getattr(request, "request_id", None)
        basic = {
            "http.request.id": request_id,
            "http.request.method": request.method,
            "url.path": request.path,
        }

        def _get_user():
            return {
                "user.id": request.user.pk if request.user else None,
                "user.name": request.user.username if request.user else None,
            }

        logger.info(
            "Request %r started: %s %s", request_id, request.method, request.path,
            extra={
                "extra": {
                    **basic,
                    **_get_user(),
                }
            }
        )
        start = time.time()
        try:
            response = get_response(request)
        except:
            duration = time.time() - start
            logger.fatal(
                "Request %r failed: duration=%.4fs",
                request_id, duration,
                extra={
                    "extra": {
                        **basic,
                        **_get_user(),
                    }
                }
            )
            raise
        else:
            duration = time.time() - start
            logger.info(
                "Request %r processed: status_code=%s, duration=%.4fs",
                request_id, duration, response.status_code,
                extra={
                    "extra": {
                        **basic,
                        **_get_user(),
                        "http.response.status_code": response.status_code,
                    }
                }
            )
        return response

    return middleware
