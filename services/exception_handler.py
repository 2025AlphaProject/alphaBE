import sys
from config.settings import APP_LOGGER
import logging
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler

logger = logging.getLogger(APP_LOGGER)

def get_my_function(depth=1):
    return sys._getframe(depth).f_code.co_name

def get_error_line(depth=1):
    return sys._getframe(depth).f_lineno

def get_error_file(depth=1):
    return sys._getframe(depth).f_code.co_filename

class ExceptionHandler(APIException):
    status_code = 400
    default_detail = f"에러 발생"
    default_code = 'error'


    def __init__(self, error_file, error_func, error_line, error_code, error_message):
        """
            :param error_file: 에러가 발생한 파일명
            :param error_func: 에러가 발생한 함수
            :param error_line: 에러가 발생한 코드 줄
            :param error_code: 에러 코드
            :param error_message: 에러 메시지
        """
        self.error_file = error_file
        self.error_func = error_func
        self.error_line = error_line
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(detail=self.get_full_details(), code=self.get_codes())

    def get_full_details(self):
        exception_str = f"error file: {self.error_file}, error_func: {self.error_func}, error_line: {self.error_line}, error_code: {self.error_code}, error_message: {self.error_message}"
        logger.warning(exception_str)
        # 코드 보안을 지키기 위해 에러 메시지만 노출합니다.
        return self.error_message

    def get_codes(self):
        return self.error_code

class ValidationException(ExceptionHandler):
    """
        Validation Exception
    """
    pass

class NoObjectException(ExceptionHandler):
    pass

class NoAttributeException(ExceptionHandler):
    pass

class NoRequiredParameterException(ExceptionHandler):
    def __init__(self, error_file, error_func, error_line, error_code=None, error_message=None):
        error_code = error_code or 'NO_REQUIRED_PARAMETER'
        error_message = error_message or '필수 파라미터 중 일부 혹은 전체가 없습니다.'
        super().__init__(error_file, error_func, error_line, error_code, error_message)

