import logging

from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from config.settings import APP_LOGGER
from config.settings import KAKAO_REFRESH_TOKEN, KAKAO_REST_API_KEY, REFRESH_TOKEN
from services.kakao_token_service import KakaoTokenService
from usr.models import User

logger = logging.getLogger(APP_LOGGER)


class BaseTestCase(TestCase):
    is_issued_token = False # 토큰 발급을 하였는가
    is_created_user = False
    @classmethod
    def setUpClass(cls):
        if cls.is_issued_token:
            return
        cls.is_issued_token = True
        super().setUpClass()
        token_service = KakaoTokenService(KAKAO_REST_API_KEY)
        sub = RefreshToken(REFRESH_TOKEN).payload['sub']
        tokens = RefreshToken.for_user(User.objects.get(sub=sub))
        kakao_tokens = token_service.get_new_tokens(KAKAO_REFRESH_TOKEN)
        cls.KAKAO_TEST_ACCESS_TOKEN = tokens.access_token
        cls.KAKAO_TEST_ID_TOKEN = kakao_tokens.id_token
        logger.debug('ACCESS_TOKEN: ' + str(cls.KAKAO_TEST_ACCESS_TOKEN))
        logger.debug('ID_TOKEN: ' + str(cls.KAKAO_TEST_ID_TOKEN))

    @classmethod
    def setUpTestData(cls):
        if not cls.is_created_user:
            user = User.objects.create(
                sub=3928446869,
                username='TestUser',
                gender='male',
                age_range='1-9',
                profile_image_url='https://example.org'
            )
            user.set_password('test_password112')
            user.save()
            cls.is_created_user = True