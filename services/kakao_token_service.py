import requests
import logging, json
from config.settings import KAKAO_REST_API_KEY, APP_LOGGER

logger = logging.getLogger(APP_LOGGER)

class KakaoTokenService:
    """
    해당 서비스는 카카오 토큰 발급에 관여하는 서비스입니다.
    """

    response = None
    status_code = None
    access_token = None
    refresh_token = None
    id_token = None
    token_type = None

    def __init__(self, kakao_rest_api_key=KAKAO_REST_API_KEY):
        self.kakao_rest_api_key = kakao_rest_api_key

    def get_new_access_token(self, refresh_token) -> str:
        """
        해당 함수는 리프레시 토큰을 이용하여 액세스 토큰을 발급할 때 사용하는 함수 입니다.
        """
        return self.get_new_access_and_refresh_token(refresh_token)[0]


    def get_new_access_and_refresh_token(self, refresh_token: str) -> tuple[str, str]:
        refresh_api_data = {
            'grant_type': 'refresh_token',
            'client_id': self.kakao_rest_api_key,
            'refresh_token': refresh_token,
        }
        response = self.get_kakao_token_response(refresh_api_data)
        if response[0] != 200:
            raise Exception(response[1])

        response = response[1]
        return response.get('access_token', None), response.get('refresh_token', None)



    def get_new_refresh_token(self, refresh_token: str) -> str:
        return self.get_new_access_and_refresh_token(refresh_token)[1]

    def get_kakao_token_response(self, data) -> tuple[int, json]:  # grant_type: access_token (default), refresh_token
        """
        해당 함수는 api 통신을 담당하며, 카카오 API와 통신을 한 결과 값 그대로를 전달합니다.
        """
        # 토클 발급 url
        token_url = 'https://kauth.kakao.com/oauth/token'
        # 요청 헤더
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        response = requests.post(token_url, data=data, headers=headers)
        if response.status_code == 200:
            self.save_object_property(response)
            return response.status_code, response.json()
        self.response = response.json()
        self.status_code = response.status_code
        return response.status_code, response.text

    def save_object_property(self, response):
        self.response = response.json()
        self.status_code = response.status_code
        self.access_token = self.response.get('access_token', None)
        self.refresh_token = self.response.get('refresh_token', None)
        self.token_type = self.response.get('token_type', None)
        self.id_token = self.response.get('id_token', None)