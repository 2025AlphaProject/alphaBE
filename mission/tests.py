from mission.models import Mission
from tour.models import Place,PlaceImages
from usr.models import User
from tour.models import TravelDaysAndPlaces
from django.core.files import File
from tour.models import Travel
from services.tour_api import NearEventInfo
from mission.services import ObjectDetection
import shutil
import tempfile
from django.test import TestCase, override_settings
import json
from django.conf import settings
from tests.base import BaseTestCase
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT, DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class TestMission(BaseTestCase):
    def __init__(self, methodName: str = "runTest"):
        super().__init__(methodName)

    def setUp(self):
        # 유저 정보 임의 생성 및 저장
        user = User.objects.create(
            sub=3935716527,
            username='TestUser',
            gender='male',
            age_range='1-9',
            profile_image_url='https://example.org'
        )
        user.set_password('test_password112')
        user.save()

        # 임의 미션 생성
        Mission.objects.create(content='예시 사진과 유사하게 사진찍기')
        Mission.objects.create(content='손 하트 만든 상태로 사진찍기')

        # 장소 생성
        self.place1 = Place.objects.create(name="사진 X 장소1", mapX=127.001, mapY=37.501)
        self.place2 = Place.objects.create(name="사진 X 장소2", mapX=127.002, mapY=37.502)
        self.place3 = Place.objects.create(name="사진 있는 장소", mapX=127.003, mapY=37.503)

    def test_mission(self):
        """
        기본 미션 리스트 조회 테스트
        """
        end_point = '/mission/list/'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)
