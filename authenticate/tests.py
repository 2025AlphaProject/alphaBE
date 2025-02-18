from django.test import TestCase
from config.settings import KAKAO_AUTH_CODE # 임시 인가 코드를 가져옵니다. 테스트 실행시마다 .env 파일에서 매번 바꿔줘야합니다.

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