from django.http import JsonResponse
from config.settings import APP_LOGGER
import logging
from services.exception_handler import ExceptionHandler
import traceback

class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger(APP_LOGGER)

    def __call__(self, request):
        try:
            return self.get_response(request)
        except ExceptionHandler as e: # 서비스가 설정한 예외를 잡은 경우
            return JsonResponse({
                'Error': e
            }, status=400)
        except Exception as e: # 예상치 못한 예외 발생한 경우
            self.logger.error(f'Exception: {e}\ntraceback: {traceback.format_exc()}')
            return JsonResponse({
                'Error': str(e)
            }, status=500)