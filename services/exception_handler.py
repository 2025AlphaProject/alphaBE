import sys
import inspect, os
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

def get_error_context(depth=1):
    frame = inspect.stack()[depth]
    return {
        "file": frame.filename,
        "func": frame.function,
        "line": frame.lineno,
    }

class ExceptionHandler(APIException):
    status_code = 400
    default_detail = f"에러 발생"
    default_code = 'error'


    def __init__(self, error_code, error_message, error_depth=2):
        """
            :param error_code: 에러 코드
            :param error_message: 에러 메시지
        """
        context = get_error_context(error_depth)
        self.error_file = context["file"]
        self.error_func = context["func"]
        self.error_line = context["line"]
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
        해당 예외는 유효성 검사에서 실패가 발생했을 시 발생하는 예외입니다
    """
    default_code = 'VALIDATION_ERROR'
    default_detail = '유효성 검사 실패.'

    def __init__(self, error_code=None, error_message=None):
        # 에러 코드와 에러 메시지는 기본값으로 보내는 것이 가능하도록 설정합니다.
        super().__init__(error_code, error_message, 3)

class NoObjectException(ExceptionHandler):
    """
        해당 예외는 요청한 Object가 존재하지 않을 때 발생하는 예외입니다.
        기본으로 404 status code를 반환합니다.

        Attributes:
            error_code (str): Custom error code identifying the error.
            error_message (str): Detailed error message describing the issue.

    """
    status_code = 404
    default_code = 'NO_OBJECT'

    def __init__(self, error_code=None, error_message=None):
        # 에러 코드와 에러 메시지는 기본값으로 보내는 것이 가능하도록 설정합니다.
        super().__init__(error_code, error_message, 3)

class NoAttributeException(ExceptionHandler):
    """
    해당 예외는 요청 객체의 속성이 없을 때 발생하는 예외입니다.

    Attributes:
        error_code (str): Custom error code identifying the error.
        error_message (str): Detailed error message describing the issue.
    """
    default_code = 'NO_ATTRIBUTE'
    default_detail = '요청한 속성이 존재하지 않습니다.'

    def __init__(self, error_code=None, error_message=None):
        # 에러 코드와 에러 메시지는 기본값으로 보내는 것이 가능하도록 설정합니다.
        super().__init__(error_code, error_message, 3)

class NoRequiredParameterException(ExceptionHandler):
    """
    해당 예외는 필수 파라미터가 존재하지 않을 때 발생하는 예외입니다.

    Attributes:
        error_code (str, optional): Custom error code identifying the error.
        error_message (str, optional): Detailed error message describing the issue.
    """
    def __init__(self, error_code=None, error_message=None):
        error_code = error_code or 'NO_REQUIRED_PARAMETER'
        error_message = error_message or '필수 파라미터 중 일부 혹은 전체가 없습니다.'
        super().__init__(error_code, error_message, 3)

class ValueException(ExceptionHandler):
    """
        해당 예외는 파라미터로 들어와야 할 데이터 타입은 올바르게 들어왔지만, 올바른 형식이 들어오지 않았을 경우에 발생하는 예외 입니다.

        Attributes:
            error_code (str, optional): Custom error code identifying the error.
            error_message (str, optional): Detailed error message describing the issue.
    """
    def __init__(self, error_code=None, error_message=None):
        error_code = error_code or 'VALUE_ERROR'
        error_message = error_message or '입력 형식이 잘못되었습니다.'
        super().__init__(
            error_code,
            error_message,
            3
        )



def custom_exception_handler(exc, context):
    """
        DRF의 커스텀 핸들러를 설정하며, detail만 메시지가 갔던 기존 방식에 비해서 status code와 같은 부가 정보를 추가해 보냅니다.
    """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code

    return response


