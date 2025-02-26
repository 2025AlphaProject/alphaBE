from django.test import TestCase
from .services import UserService
from config.settings import KAKAO_TEST_ID_TOKEN
from .models import User
# Create your tests here.

class TestService(TestCase):

    def test_user_service(self):
        """
        해당 테스트는 유저 서비스를 테스트 하기 위한 테스트 코드입니다.
        """
        user_service = UserService(KAKAO_TEST_ID_TOKEN) # 테스트 아이디 토큰으로 유저 서비스 생성
        user = user_service.get_or_register_user()
        self.assertNotEqual(user, None)
