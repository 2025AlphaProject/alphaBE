from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from mission.models import Mission
from tour.models import TravelDaysAndPlaces, Place

class TestMissionViews(TestCase):
    def setUp(self):
        """
        테스트를 위한 초기 데이터 설정
        """
        self.client = APIClient()

        # 사용자 생성 및 인증
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.force_authenticate(user=self.user)

        # 미션 생성
        self.mission = Mission.objects.create(content='예시 사진과 유사하게 사진찍기')

        # 여행 및 장소 데이터 생성
        self.place = Place.objects.create(id=1, name='테스트 장소')
        self.travel_days_and_places = TravelDaysAndPlaces.objects.create(id=1, mission=self.mission)

        # 업로드할 이미지 파일 생성
        self.image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

    def test_mission_list(self):
        """
        미션 목록 조회 테스트
        """
        end_point = '/mission/list/'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        print("✅ 미션 목록 조회 테스트 성공")

    def test_mission_image_upload(self):
        """
        미션 이미지 업로드 테스트
        """
        end_point = '/mission/image_upload/'
        data = {
            'travel_days_id': self.travel_days_and_places.id,
            'image': self.image
        }
        response = self.client.post(end_point, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('mission_image_url', response.data)
        print("✅ 미션 이미지 업로드 테스트 성공")

    def test_mission_check_complete(self):
        """
        미션 성공 여부 확인 테스트
        """
        end_point = '/mission/check_complete/'
        data = {
            "travel_days_id": self.travel_days_and_places.id,
            "place_id": self.place.id,
            "mission_id": self.mission.id
        }
        response = self.client.post(end_point, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("similarity_score", response.data)
        self.assertIn("mission_success", response.data)
        print("✅ 미션 성공 여부 확인 테스트 성공")
