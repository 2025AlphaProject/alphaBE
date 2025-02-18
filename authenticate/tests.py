from django.test import TestCase
from config.settings import (KAKAO_AUTH_CODE, # 임시 인가 코드를 가져옵니다. 테스트 실행시마다 .env 파일에서 매번 바꿔줘야합니다.
                             KAKAO_REFRESH_TOKEN # 리프레시 토큰. 만료시 바꿔 사용
                             )

# Create your tests here.

class TestAuthenticate(TestCase):
    AUTH_CODE = KAKAO_AUTH_CODE # TODO 인가코드를 말하며, 테스트 진행시마다 바꿔줘야합니다.
    def test_login_callback(self):
        """
        해당 테스트는 카카오 로그인 콜백이 정상적으로 이루어지는지 확인하기 위한 코드입니다.
        """
        redirect_uri = 'http://localhost:8000/auth/login/'
        response = self.client.post(f'/auth/login/?code={self.AUTH_CODE}&redirect_uri={redirect_uri}')
        print(response.json())
        self.assertEqual(response.status_code, 201)

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
        print(response.json())
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
