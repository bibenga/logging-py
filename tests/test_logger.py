import logging
import pytest

from barnlog.requests import LoggedSession


@pytest.mark.django_db(transaction=True)
class TestWorker:
    def test__exception(self, mocker):
        log = logging.getLogger("olala")
        try:
            raise RuntimeError("Olala")
        except:
            log.error("olala", exc_info=True)

    def test_requests(self, requests_mock):
        requests_mock.get('https://httpbin.org/headers', text='data')
        s = LoggedSession()
        s.get('https://httpbin.org/headers', headers={'x-test2': 'true'})
