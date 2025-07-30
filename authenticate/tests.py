import logging
import unittest

from django.test import override_settings
from django.urls import reverse

from config.settings import (
    KAKAO_AUTH_CODE,  # 임시 인가 코드를 가져옵니다. 테스트 실행시마다 .env 파일에서 매번 바꿔줘야합니다.
    # 리프레시 토큰. 만료시 바꿔 사용
    APP_LOGGER,
    SKIP_TEST,
    SIMPLE_JWT,
    REFRESH_TOKEN,
)
from tests.base import BaseTestCase

logger = logging.getLogger(APP_LOGGER)

# Create your tests here.

class TestAuthenticate(BaseTestCase):
    AUTH_CODE = KAKAO_AUTH_CODE # TODO 인가코드를 말하며, 테스트 진행시마다 바꿔줘야합니다.

    @unittest.skipIf(SKIP_TEST == 'True', "Skip Login Callback Test")
    def test_login_callback(self):
        """
        해당 테스트는 카카오 로그인 콜백이 정상적으로 이루어지는지 확인하기 위한 코드입니다.
        """
        redirect_uri = 'http://localhost:8000/auth/login/'
        response = self.client.post(f'/auth/get_token/?code={self.AUTH_CODE}&redirect_uri={redirect_uri}')
        print(response.json())
        self.assertEqual(response.status_code, 201)

    # python의 unpacking은 같은 값이 있다면 덮어쓰기로 진행이 됨. 따라서 BLACKLIST_AFTER_ROTATION값은 False로 됨
    # 아래 설정은 리프레시 토큰은 테스트 중에는 블랙리스트에 넣지 않도록 함
    @override_settings(SIMPLE_JWT={**SIMPLE_JWT, "BLACKLIST_AFTER_ROTATION": False})
    def test_refresh_token_success(self):
        """
            해당 테스트는 토큰이 제대로 refresh가 되는지 테스트합니다.
        """
        uri = reverse('refresh')
        data = {
            'refresh_token': REFRESH_TOKEN,
        }
        response = self.client.post(uri, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        logger.debug('test_refresh_token_success result:' + str(response.json()))

    def test_refresh_token_failure_no_parameter(self):
        """
            해당 테스트는 refresh token 뷰에서 파라미터가 제대로 날라오지 않았을 경우를 테스트합니다.
        """
        uri = reverse('refresh')
        data = {
            'ref': '123sdf1',
        }
        response = self.client.post(uri, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        logger.debug('refresh no parameter result:' + str(response.json()))

    def test_refresh_token_failure_invalid_token(self):
        """
            해당 테스트는 refresh token 뷰에서 토큰이 유효하지 않은 경우를 테스트합니다.
        """
        uri = reverse('refresh')
        data = {
            'refresh_token': '1pbZZHeOq9TsJBPQgA-URNdOUoDlhxp__AAAAAgo9cusAAAGUKtVQgeQ1KlcE_6bt',
        }
        response = self.client.post(uri, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        logger.debug('refresh invalid token result:' + str(response.json()))


    def test_login_success(self):
        """
        해당 함수는 flutter sdk로 발급받은 액세스 토큰과 아이디 토큰을 활용하여 로그인 혹은 회원가입 진행이 되는지 확인합니다.
        """
        end_point = reverse('login_register')
        headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}'
        }
        data = {
            'id_token': self.KAKAO_TEST_ID_TOKEN,
        }
        # register Test
        response = self.client.post(end_point, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # login Test
        response = self.client.post(end_point, headers=headers, data=data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['is_new'], False)
        logger.debug('login success result:' + str(response.json()))

    def test_login_failure(self):
        """
            로그인 실패를 테스트합니다.
        """
        end_point = reverse('login')
        headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}'
        }
        # 400 Test
        data2 = {
            'id_token': 'hsesefs'
        }
        response = self.client.post(end_point, headers=headers, data=data2, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        logger.debug('login failure result:' + str(response.json()))
