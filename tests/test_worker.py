import pytest


@pytest.mark.django_db(transaction=True)
class TestWorker:
    async def test__process(self, mocker):
        pass
