import json
import logging

from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger("ingest")


@csrf_exempt
def log_ingest(request: HttpRequest) -> HttpResponse:
    body = request.body
    msg = "<empty>"
    if body:
        try:
            data = json.loads(body)
            msg = json.dumps(data)
        except (ValueError, TypeError):
            try:
                msg = body.decode()
            except (ValueError, TypeError):
                msg = body
    logger.info("%s", msg)
    return HttpResponse()
