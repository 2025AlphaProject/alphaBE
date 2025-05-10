import requests
from config.settings import (
    KAKAO_REAL_REST_API_KEY,
    KAKAO_REAL_NATIVE_API_KEY,
    KAKAO_REAL_JAVASCRIPT_KEY,
    KAKAO_ADMIN_KEY
)
from .kakao_error_handler import (
    KakaoHttpClientException,
    KakaoRequestError
)
from .error_handler import (
    get_my_function,
    get_error_line
)



class KakaoHttpClient:
    """
        해당 클래스는 카카오 API와 통신을 담당하는 클래스입니다.
        해당 클래스에서는 카카오 API와 통신한 결과값을 그대로 반환합니다.
    """
    def __init__(self,
                 kakao_native_app_key=KAKAO_REAL_NATIVE_API_KEY,
                 kakao_rest_api_key=KAKAO_REAL_REST_API_KEY,
                 kakao_javascript_key=KAKAO_REAL_JAVASCRIPT_KEY,
                 kakao_admin_key=KAKAO_ADMIN_KEY,
                 ):
        self.__kakao_native_app_key = kakao_native_app_key
        self.__kakao_rest_api_key = kakao_rest_api_key
        self.__kakao_javascript_key = kakao_javascript_key
        self.__kakao_admin_key = kakao_admin_key


    def get_token_refresh_response(self, refresh_token, kakao_api_key=None):
        """
            해당 함수는 카카오 토큰 갱신 응답을 반환합니다.
            :param refresh_token: 카카오에서 발급받은 refresh_token
            :param kakao_api_key: kakao_api_key를 의미하면 기본값은 실제 커네버의 rest api키로 들어갑니다.
        """
        return self.__get_token_response(
            grant_type='refresh_token',
            kakao_api_key=kakao_api_key,
            refresh_token=refresh_token,
        )

    def get_token_response(self, auth_code, redirect_uri, kakao_rest_api_key=None):
        return self.__get_token_response(
            grant_type='authorization_code',
            kakao_rest_api_key=kakao_rest_api_key,
            code=auth_code,
            redirect_uri=redirect_uri,
        )



    def __get_token_response(self, grant_type='refresh_token', kakao_api_key=None, **kwargs):
        token_url = 'https://kauth.kakao.com/oauth/token'
        # 요청 헤더
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        data = {
            'grant_type': grant_type,
            'client_id': kakao_api_key or self.__kakao_rest_api_key,
        }
        if grant_type == 'authorization_code':
            data['redirect_uri'] = kwargs.get('redirect_uri')
            data['code'] = kwargs.get('code')
        elif grant_type == 'refresh_token':
            data['refresh_token'] = kwargs.get('refresh_token')
        else:
            raise KakaoHttpClientException(
                get_my_function(),
                get_error_line(),
                400,
                f'grant_type: {grant_type} is not supported.'
            )
        # 실제 요청 발송
        response = requests.post(token_url, data=data, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            # 요청 잘못으로 판단
            raise KakaoRequestError(
                get_my_function(),
                get_error_line(),
                response.status_code,
                response.text
            )
        # 카카오 오류 발생
        raise KakaoHttpClientException(
            get_my_function(),
            get_error_line(),
            response.status_code,
            response.text
        )

    def get_kakao_user_info(self, sub: int, kakao_admin_key=None):
        """
            해당 함수는 카카오 유저의 정보를 가져오는 함수 입니다.
        """
        kakao_user_info_url = f'https://kapi.kakao.com/v2/user/me?target_id_type=user_id&target_id={sub}'

        header = {
            'Authorization': f'KakaoAK {kakao_admin_key or self.__kakao_admin_key}', # 함수 파라미터 우선
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        response = requests.get(kakao_user_info_url, headers=header)  # 요청을 받아옵니다.
        if response.status_code == 200: # 정상적인 요청이라면
            return response.json()
        elif response.status_code // 100 == 4: # 400번대 인경우
            raise KakaoRequestError(
                get_my_function(),
                get_error_line(),
                response.status_code,
                response.text
            )

        raise KakaoHttpClientException(
            get_my_function(),
            get_error_line(),
            response.status_code,
            response.text
        )



if __name__ == "__main__":
    kakao_http_client = KakaoHttpClient()