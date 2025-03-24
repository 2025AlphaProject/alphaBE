from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from mission.models import Mission
from tour.models import TravelDaysAndPlaces, Place, PlaceImages, Travel
from django.urls import reverse
from django.contrib.auth import get_user_model
from datetime import date

from django.conf import settings
import os

class TestMission(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            sub=123456789012345678,  # 필수
            username="testuser",
            email="test@example.com",
            password="testpassword",
            gender="male",
            age_range="20-29",
            profile_image_url="https://example.com/profile.jpg"
        )

        self.mission1 = Mission.objects.create(content='예시 사진과 유사하게 사진찍기')
        self.place = Place.objects.create(name="Test Place", mapX=127.001, mapY=37.501)

        self.place_image = PlaceImages.objects.create(
            place=self.place,
            image_url="https://upload.wikimedia.org/wikipedia/commons/5/5f/Alberta_-_Jasper_National_Park.jpg"
        )

        self.travel = Travel.objects.create(
            user=self.user,
            tour_name="부산여행",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 3)
        )

        self.travel_day = TravelDaysAndPlaces.objects.create(
            travel=self.travel,
            place=self.place,
            date=date(2024, 1, 1),
            mission=self.mission1
        )

    def test_mission_list_api(self):
        """ 미션 리스트 GET 테스트 """
        end_point = '/mission/list/'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)
        print(response.json())

    def test_image_upload_api(self):
        """ 미션 이미지 업로드 POST 테스트 """
        url = '/mission/image_upload/'

        # 테스트용 이미지 업로드 준비
        test_image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")

        data = {
            'travel_days_id': self.travel_day.id,
            'image': test_image,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        print(response.json())

    def test_mission_check_api(self):
        """ 미션 성공 여부 확인 테스트 """
        # 먼저 테스트 이미지를 travel_day에 수동으로 할당
        from django.core.files.base import ContentFile
        self.travel_day.mission_image.save('dummy.jpg', ContentFile(b"dummy_content"), save=True)

        url = '/mission/check_complete/'

        data = {
            "travel_days_id": self.travel_day.id,
            "place_id": self.place.id,
            "mission_id": self.mission1.id,
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        print(response.json())

