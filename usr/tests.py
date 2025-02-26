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
        # 아래 코드는 유저가 없는 상태에서 회원가입을 진행할 때를 가정한 테스트입니다.
        user_service = UserService(KAKAO_TEST_ID_TOKEN) # 테스트 아이디 토큰으로 유저 서비스 생성
        user = user_service.get_or_register_user()
        self.assertIsInstance(user[0], User) # 해당 객체가 유저에 속하는 인스턴스인지 파악합니다.

        # 아래 코드는 유저가 있는 상태에서 실제로 회원이 들어오는지 확인하는 테스트입니다.
        user_service = UserService(KAKAO_TEST_ID_TOKEN) # 테스트 아이디 토큰으로 유저 서비스 객체를 생성
        exist_user = user_service.get_or_register_user()
        self.assertIsInstance(exist_user[0], User) # 해당 객체가 유저에 속하는 인스턴스인지 파악합니다.
