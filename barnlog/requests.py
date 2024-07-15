import logging

import requests

logger = logging.getLogger(__name__)

# from barnlog.requests import LoggedSession
# s = LoggedSession()
# s.get('https://httpbin.org/headers', headers={'x-test2': 'true'})


class LoggedSession(requests.Session):
    def __init__(self, with_body: bool = True, logger: logging.Logger = logger) -> None:
        super().__init__()
        self.logger = logger
        self.with_body = with_body

    def send(self, request: requests.PreparedRequest, **kwargs):
        basic = {
            "url.full": request.url,
            "http.request.method": request.method,
        }
        self.logger.info(
            "send http request %s %s", request.method,
            request.url,
            extra={
                "extra": {
                    **basic,
                    "http.request.body.content": self._get_request_body(request),
                }
            }
        )

        try:
            response = super().send(request, **kwargs)
        except requests.RequestException as e:
            response = e.response
            if response is not None:
                self.logger.fatal(
                    "http request is failed: %s %s", response.status_code, request.url,
                    extra={
                        "extra": {
                            **basic,
                            "http.response.status_code": response.status_code,
                            "http.response.body.content": self._get_response_body(response),
                        }
                    }
                )
            else:
                self.logger.fatal(
                    "http request failed: %s", request.url,
                    extra={
                        "extra": basic
                    }
                )
            raise
        except:
            self.logger.fatal(
                "http request failed: %s", request.url,
                extra={
                    "extra": basic
                }
            )
            raise
        else:
            self.logger.info(
                "http request completed successfully: %s %s",
                response.status_code, request.url,
                extra={
                    "extra": {
                        **basic,
                        "http.response.status_code": response.status_code,
                        "http.response.body.content": self._get_response_body(response),
                    }
                }
            )
        return response

    def _get_request_body(self, request):
        if self.with_body:
            return str(request.body)
        else:
            return "<hidden>"

    def _get_response_body(self, response):
        if self.with_body:
            if response is not None:
                return response.text
        else:
            return "<hidden>"
