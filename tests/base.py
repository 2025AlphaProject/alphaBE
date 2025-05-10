from django.test import TestCase
from services.kakao_token_service import KakaoTokenService
from config.settings import KAKAO_REFRESH_TOKEN, KAKAO_REST_API_KEY

class BaseTestCase(TestCase):
    is_issued_token = False # 토큰 발급을 하였는가
    @classmethod
    def setUpClass(cls):
        if cls.is_issued_token:
            return
        cls.is_issued_token = True
        super().setUpClass()
        token_service = KakaoTokenService(KAKAO_REST_API_KEY)
        tokens = token_service.get_new_tokens(KAKAO_REFRESH_TOKEN)
        cls.KAKAO_TEST_ACCESS_TOKEN = tokens.access_token
        cls.KAKAO_TEST_ID_TOKEN = tokens.id_token