from typing import Optional
import requests
import logging, json
from config.settings import KAKAO_REST_API_KEY, APP_LOGGER
from .exception_handler import (
    get_my_function,
    get_error_line
)
from .kakao_http_client import (
    KakaoHttpClient
)
from .kakao_error_handler import (
    KakaoServerError
)
from dataclasses import dataclass

logger = logging.getLogger(APP_LOGGER)

@dataclass
class TokenData:
    access_token: Optional[str]
    refresh_token: Optional[str]
    id_token: Optional[str]
    token_type: Optional[str]

class KakaoTokenService:
    """
    해당 서비스는 카카오 토큰 발급에 관여하는 서비스입니다.
    """

    def __init__(self, kakao_api_key=KAKAO_REST_API_KEY):
        self.kakao_api_key = kakao_api_key

    def get_new_access_token(self, refresh_token) -> str:
        """
        해당 함수는 리프레시 토큰을 이용하여 액세스 토큰을 발급할 때 사용하는 함수 입니다.
        """
        return self.get_new_tokens(refresh_token).access_token


    def get_new_tokens(self, refresh_token: str) -> TokenData:
        """
            해당 함수는 refresh token을 이용하여 카카오 토큰을 갱신하여 토큰을 반환하는 함수입니다.
            :param refresh_token: 카카오에서 발급 받은 리프레시 토큰입니다.
            :return: TokenData를 반환합니다.
        """
        kakao_http_client = KakaoHttpClient()
        response = kakao_http_client.get_token_refresh_response(refresh_token, self.kakao_api_key)
        # 객체 내 토큰 저장
        return self.__validate_token_response(response)

    def get_tokens(self, auth_code: str, redirect_uri: str) -> TokenData:
        kakao_http_client = KakaoHttpClient(
            kakao_rest_api_key=self.kakao_api_key
        )
        response = kakao_http_client.get_token_response(auth_code, redirect_uri, self.kakao_api_key)
        # 토큰 반환
        return self.__validate_token_response(response)



    def get_new_refresh_token(self, refresh_token: str) -> str:
        """
            해당 함수는 리프레시 토큰만 가져오는 역할을 합니다.
            :param refresh_token: 카카오에서 발급 받은 리프레시 토큰입니다.
        """
        return self.get_new_tokens(refresh_token).refresh_token

    def __validate_token_response(self, response_json):
        if response_json.get('access_token') is None or\
            response_json.get('id_token') is None or\
            response_json.get('token_type') is None:
            raise KakaoServerError(
                get_my_function(),
                get_error_line(),
                'kakao server exception',
                f'토큰 응답 결과: {response_json}'
            )

        # TokenData 리턴
        return TokenData(
            access_token=response_json.get('access_token', None),
            refresh_token=response_json.get('refresh_token', None),
            id_token=response_json.get('id_token', None),
            token_type=response_json.get('token_type', None),
        )
