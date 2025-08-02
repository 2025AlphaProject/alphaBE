import logging

from config.settings import APP_LOGGER

logger = logging.getLogger(APP_LOGGER) # 로그 설정

class KakaoHttpClientException(Exception):
    """
        카카오에서 날라온 예외를 반환하는 코드입니다.
    """
    def __init__(self, error_func, error_line, error_code, error_message):
        self.error_func = error_func # 에러가 발생한 함수입니다.
        self.error_line = error_line # 에러가 발생한 코드 라인입니다. 유지 보수성을 높이기 위해 도입합니다.
        self.error_code = error_code
        self.error_message = error_message

    def __str__(self):
        logger.warning(f"카카오 API 통신 오류. error_code: {self.error_code}, error_message: {self.error_message}")
        return f"error_code: {self.error_code}, error_message: {self.error_message}"

class KakaoServerError(KakaoHttpClientException):
    """
        해당 예외는 카카오에서 제대로 된 값을 주지 못했을 경우 발생하는 오류 입니다.
    """

    def __str__(self):
        logger.warning(f"카카오 서버 오류 의심. 호출 함수: {self.error_func}. error_message: {self.error_message}")
        return f"kakao server error. error_message: {self.error_message}"

class KakaoRequestError(KakaoHttpClientException):
    """
        해당 예외는 사용자가 잘못 요청을 보냈을 경우 발생하는 예외입니다.
    """

    def __str__(self):
        logger.info(f'Kakao Request Error. Error Function: {self.error_func}. Error Message: {self.error_message}')
        return f'Kakao Request Error: {self.error_message}'
