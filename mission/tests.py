from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from config.settings import KAKAO_TEST_ACCESS_TOKEN
from mission.models import Mission
from tour.models import TravelDaysAndPlaces, Place, PlaceImages, Travel
from django.contrib.auth import get_user_model
from datetime import date
from django.core.files.base import ContentFile

class TestMission(TestCase):
    def setUp(self):
        # 임의로 미션을 생성합니다.
        Mission.objects.create(
            content='예시 사진과 유사하게 사진찍기'
        )
        Mission.objects.create(
            content='손 하트 만든 상태로 사진찍기'
        )
    def test_mission(self):
        """
        기본 미션 리스트 조회 테스트
        """
        end_point = '/mission/list/'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)
        print(response.json())

    def test_mission_random_create_api(self):
        """
        사진이 없는 장소(place)에 대해 임의 미션을 생성하는 POST API 테스트입니다.
        """
        url = '/mission/random/'

        headers = {
            'Authorization': f'Bearer {KAKAO_TEST_ACCESS_TOKEN}',
        }

        data = {
            "places": [
                {"place_id": self.place1.id, "image_url": ""},
                {"place_id": self.place2.id, "image_url": ""},
                {"place_id": self.place3.id, "image_url": "https://example.com/image.jpg"}
            ]
        }

        response = self.client.post(url, data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertIn("missions", response.json())
        self.assertEqual(len(response.json()["missions"]), 2)

        print("랜덤 미션 생성 응답:", response.json())