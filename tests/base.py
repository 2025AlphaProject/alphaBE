from django.test import TestCase
from authenticate.services import KakaoTokenService
from config.settings import KAKAO_REFRESH_TOKEN, KAKAO_REST_API_KEY

class BaseTestCase(TestCase):
    is_issued_token = False # 토큰 발급을 하였는가
    @classmethod
    def setUpClass(cls):
        if cls.is_issued_token:
            return
        cls.is_issued_token = True
        super().setUpClass()
        token_service = KakaoTokenService()
        data = {
            'grant_type': 'refresh_token',
            'client_id': KAKAO_REST_API_KEY,
            'refresh_token': KAKAO_REFRESH_TOKEN,
        }
        token_service.get_kakao_token_response(data)
        cls.KAKAO_TEST_ACCESS_TOKEN = token_service.access_token
        cls.KAKAO_TEST_ID_TOKEN = token_service.id_token