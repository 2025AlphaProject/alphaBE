import sys
from config.settings import APP_LOGGER
import logging

logger = logging.getLogger(APP_LOGGER)

def get_my_function(depth=1):
    return sys._getframe(depth).f_code.co_name

def get_error_line(depth=1):
    return sys._getframe(depth).f_lineno

class ExceptionHandler(Exception):

    def __init__(self, error_func, error_line, error_code, error_message):
        """
            :param error_func: 에러가 발생한 함수
            :param error_line: 에러가 발생한 코드 줄
            :param error_code: 에러 코드
            :param error_message: 에러 메시지
        """
        self.error_func = error_func
        self.error_line = error_line
        self.error_code = error_code
        self.error_message = error_message

    def __str__(self):
        exception_str = f"error_func: {self.error_func},\
                          error_line: {self.error_line},\
                          error_code: {self.error_code},\
                          error_message: {self.error_message}"
        logger.warning(exception_str)
        return exception_str

class ValidationException(ExceptionHandler):
    """
        Validation Exception
    """
    pass

class NoObjectException(ExceptionHandler):
    pass

class NoAttributeException(ExceptionHandler):
    pass


