import logging
from config.settings import APP_LOGGER

logger = logging.getLogger(APP_LOGGER)

class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        logger.info(
            f"{request.method} {request.path} - {response.status_code} - {request.META.get('REMOTE_ADDR')}"
        )
        return response
