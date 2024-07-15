import json
import logging
from datetime import UTC, datetime
from typing import Mapping

import requests

log = logging.getLogger("barnlog.http_client")


# from barnlog.requests import LoggedSession
# s = LoggedSession()
# s.get('https://httpbin.org/headers', headers={'x-test2': 'true'})

class LoggedSession(requests.Session):
    sensitive_headers = ["authorization", "cookie"]

    def __init__(self, with_body: bool = True, log: logging.Logger = log) -> None:
        super().__init__()
        self.log = log
        self.with_body = with_body

    def send(self, request: requests.PreparedRequest, **kwargs):
        extra = {
            "request": {
                "moment": datetime.now(UTC).isoformat(),
                "method": request.method,
                "url": request.url,
                "headers": self._get_headers(request.headers),
                "data": self._get_request_body(request),
            }
        }
        self.log.info("http send %s %s", request.method, request.url,
                      extra={"extra": extra})
        if self.log.isEnabledFor(logging.DEBUG):
            self.log.debug("request: %s", self._dumps(extra["request"]))

        try:
            response = super().send(request, **kwargs)
        except requests.RequestException as e:
            response = e.response
            if response is not None:
                extra["response"] = {
                    "moment": datetime.now(UTC).isoformat(),
                    "elapsed": response.elapsed,
                    "status_code": response.status_code,
                    "headers": self._get_headers(response.headers),
                    "data": self._get_response_body(e.response),
                }
                self.log.fatal("request is failed: %s %s", response.status_code, request.url,
                               extra={"extra": extra})
                if self.log.isEnabledFor(logging.DEBUG):
                    self.log.debug("response: %s", self._dumps(extra["response"]))
            else:
                extra["response"] = {
                    "moment": datetime.now(UTC).isoformat(),
                }
                self.log.fatal("request is failed: %s", request.url,
                               extra={"extra": extra})
                if self.log.isEnabledFor(logging.DEBUG):
                    self.log.debug("response: %s", self._dumps(extra["response"]))
            raise
        except:
            extra["response"] = {
                "moment": datetime.now(UTC).isoformat(),
            }
            self.log.fatal("request is failed: %s", request.url,
                           extra={"extra": extra})
            if self.log.isEnabledFor(logging.DEBUG):
                self.log.debug("response: %s", self._dumps(extra["response"]))
            raise
        else:
            extra["response"] = {
                "moment": datetime.now(UTC).isoformat(),
                "elapsed": response.elapsed.total_seconds(),
                "status_code": response.status_code,
                "headers": self._get_headers(response.headers),
                "data": self._get_response_body(response),
            }
            self.log.info("request is success: %s %s", response.status_code, request.url,
                          extra={"extra": extra})
            if self.log.isEnabledFor(logging.DEBUG):
                self.log.debug("response: %s", self._dumps(extra["response"]))
        return response

    def _get_headers(self, headers: Mapping) -> str | dict[str, str]:
        if self.with_body:
            return {
                name: value
                for name, value in headers.items()
                if not self._is_sensitive_header(name)
            }
        else:
            return "<sensitive>"

    def _is_sensitive_header(self, name: str) -> bool:
        if self.log.isEnabledFor(logging.DEBUG):
            return False
        return name.lower() in self.sensitive_headers

    def _get_request_body(self, request):
        if self.with_body:
            ctype = request.headers.get("content-type")
            if ctype and ctype.startswith("application/json"):
                try:
                    return json.loads(request.body)
                except:
                    return str(request.body)
            else:
                return str(request.body)
        else:
            return "<sensitive>"

    def _get_response_body(self, response):
        if self.with_body:
            if response is not None:
                ctype = response.headers.get("content-type")
                if ctype and ctype.startswith("application/json"):
                    try:
                        return response.json()
                    except:
                        return response.text
                else:
                    return response.text
        else:
            return "<sensitive>"

    def _dumps(self, data: dict) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False)
