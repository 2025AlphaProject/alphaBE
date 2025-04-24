import os, unittest
from django.test import TestCase
from config.settings import (
    KAKAO_AUTH_CODE, # 임시 인가 코드를 가져옵니다. 테스트 실행시마다 .env 파일에서 매번 바꿔줘야합니다.
    KAKAO_REFRESH_TOKEN, # 리프레시 토큰. 만료시 바꿔 사용
    # KAKAO_TEST_ACCESS_TOKEN,
    # KAKAO_TEST_ID_TOKEN,
    APP_LOGGER,
    SKIP_TEST,
    KAKAO_REST_API_KEY,
)
import logging
from .services import KakaoTokenService
logger = logging.getLogger(APP_LOGGER)

# Create your tests here.

class TestAuthenticate(TestCase):
    AUTH_CODE = KAKAO_AUTH_CODE # TODO 인가코드를 말하며, 테스트 진행시마다 바꿔줘야합니다.
    def setUp(self):
        token_service = KakaoTokenService()
        data = {
            'grant_type': 'refresh_token',
            'client_id': KAKAO_REST_API_KEY,
            'refresh_token': KAKAO_REFRESH_TOKEN,
        }
        token_service.get_kakao_token_response(data)
        self.KAKAO_TEST_ACCESS_TOKEN = token_service.access_token
        self.KAKAO_TEST_ID_TOKEN = token_service.id_token

    @unittest.skipIf(SKIP_TEST == 'True', "Skip Login Callback Test")
    def test_login_callback(self):
        """
        해당 테스트는 카카오 로그인 콜백이 정상적으로 이루어지는지 확인하기 위한 코드입니다.
        """
        redirect_uri = 'http://localhost:8000/auth/login/'
        response = self.client.post(f'/auth/get_token/?code={self.AUTH_CODE}&redirect_uri={redirect_uri}')
        self.assertEqual(response.status_code, 201)
        print(response.json())

    @unittest.skipIf(SKIP_TEST == 'True', "Skip Login Refresh Test")
    def test_refresh_token(self):
        """
        해당 테스트는 카카오 리프레시 토큰이 제대로 날라오는지 확인하기 위한 테스트입니다.
        """
        target_uri = '/auth/refresh/'
        # TODO 리프레시 토큰으로서 유효기간이 만료되면 바꿔줘야합니다.
        data = {
            'refresh_token': KAKAO_REFRESH_TOKEN,
        }
        response = self.client.post(target_uri, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        # 리프레시 토큰 정보를 body에서 발견하지 못한 경우를 테스트 합니다.
        data = {
            # 일부러 틀린 정보를 넣습니다.
            'ref': '',
        }
        response = self.client.post(target_uri, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        # 토큰 정보 자체를 변환해서 테스트합니다.
        data = {
            'refresh_token': '1pbZZHeOq9TsJBPQgA-URNdOUoDlhxp__AAAAAgo9cusAAAGUKtVQgeQ1KlcE_6bt',
        }
        response = self.client.post(target_uri, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_login(self):
        """
        해당 함수는 flutter sdk로 발급받은 액세스 토큰과 아이디 토큰을 활용하여 로그인 혹은 회원가입 진행이 되는지 확인합니다.
        """
        end_point = '/auth/login/'
        headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}'
        }
        data = {
            'id_token': self.KAKAO_TEST_ID_TOKEN,
        }
        # register Test
        response = self.client.post(end_point, headers=headers, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['is_new'], True)

        # login Test
        response = self.client.post(end_point, headers=headers, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['is_new'], False)

        # 400 Test
        data2 = {
            'id_token' : 'hsesefs'
        }
        response = self.client.post(end_point, headers=headers, data=data2, content_type='application/json')
        self.assertEqual(response.status_code, 400)

