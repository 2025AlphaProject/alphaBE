from django.test import TestCase
from .services import UserService
from config.settings import KAKAO_REFRESH_TOKEN, KAKAO_REST_API_KEY
from .models import User
from services.kakao_token_service import KakaoTokenService
from tests.base import BaseTestCase
# Create your tests here.

class TestService(BaseTestCase):
    def setUp(self):
        """
        테스트 환경에서 꼭 필요한 데이터를 업로드 하기 위한 메소드 입니다.
        """
        # 유저 정보 임의 생성
        user = User.objects.create(
            sub=3928446869, # 앱 키에 따라 내 고유 정보가 달라짐
            username='TestUser',
            gender='male',
            age_range='1-9',
            profile_image_url='https://example.org'
        )
        user.set_password('test_password112')
        user.save()

        user2 = User.objects.create(
            sub=1,
            username='TestUser2',
            gender='male',
            age_range='1-9',
            profile_image_url='https://example.org'
        )
        user2.set_password('test_password112')
        user2.save()

    def test_user_service(self):
        """
        해당 테스트는 유저 서비스를 테스트 하기 위한 테스트 코드입니다.
        """
        # 아래 코드는 유저가 없는 상태에서 회원가입을 진행할 때를 가정한 테스트입니다.
        user_service = UserService(self.KAKAO_TEST_ID_TOKEN) # 테스트 아이디 토큰으로 유저 서비스 생성
        user = user_service.get_or_register_user()
        self.assertIsInstance(user[0], User) # 해당 객체가 유저에 속하는 인스턴스인지 파악합니다.

        # 아래 코드는 유저가 있는 상태에서 실제로 회원이 들어오는지 확인하는 테스트입니다.
        user_service = UserService(self.KAKAO_TEST_ID_TOKEN) # 테스트 아이디 토큰으로 유저 서비스 객체를 생성
        exist_user = user_service.get_or_register_user()
        self.assertIsInstance(exist_user[0], User) # 해당 객체가 유저에 속하는 인스턴스인지 파악합니다.

    def test_who(self):
        """
        해당 테스트는 유저 정보 api로, 유저 DB에서 정상적으로 송신이 되는지 확인하기 위한 테스트 코드 입니다.
        """
        # 정상적으로 유저 정보가 날라오기 위한 테스트 코드입니다.
        end_point = '/user/me/'
        headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}'
        }
        response = self.client.get(end_point, headers=headers)
        self.assertEqual(response.status_code, 200) # 200이 맞는지 확인합니다.

    def test_user_list(self):
        end_point = '/user/?user_name=TestUser2'
        headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}'
        }
        response = self.client.get(end_point, headers=headers)
        self.assertEqual(response.status_code, 200)
