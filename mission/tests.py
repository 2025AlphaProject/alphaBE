from tour.models import Place,PlaceImages
import io
import logging
import tempfile

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from config.settings import APP_LOGGER
from tests.base import BaseTestCase
from tour.models import Place, PlaceImages
from tour.models import Travel
from tour.models import TravelDaysAndPlaces
from usr.models import User

logger = logging.getLogger(APP_LOGGER)

class TestMission(BaseTestCase):

    @classmethod
    def setUpTestData(cls):
        """
            테스트에 필요한 테스트 인스턴스를 구축합니다.
        """
        super().setUpTestData()
        place = Place.objects.create(
            name="test place",
            mapX="136.1",
            mapY="136.2",
        )
        PlaceImages.objects.create(
            place_id=place.id,
            image_url = "http://tong.visitkorea.or.kr/cms/resource/82/3084482_image2_1.JPG"
        )
        travel = Travel.objects.create(
            tour_name="test tour",
            tour_date='2025-07-30',
        )
        travel.user.add(User.objects.get(sub=3928446869))
        tdp = TravelDaysAndPlaces.objects.create(
            travel_id=travel.id,
            place_id=place.id,
        )

    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_mission_image_upload_success(self):
        """
            미션 이미지 업로드 테스트
        """
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), (255, 0, 0))
        image.save(file, 'JPEG')
        file.seek(0)
        image =  SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')
        uri = reverse('mission_image_upload')
        data = {
            'image': image,
            'travel_days_id': TravelDaysAndPlaces.objects.first().id,
        }
        headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}'
        }
        response = self.client.post(uri, data=data, headers=headers, format='multipart')
        self.assertEqual(response.status_code, 201)
        logger.debug('result: ' + str(response.content))

    def test_mission_evaluation_success(self):
        """
            미션 판단 조사
        """
        pass

    def test_mission_evaluation_failure(self):
        """
            미션 실패 판단 테스트
        """
        uri = reverse('mission_check')
        self.test_mission_image_upload_success()
        tdp = TravelDaysAndPlaces.objects.first()
        data = {
            'travel_id': tdp.travel_id,
            'place_id': tdp.place_id,
            'mission_id': 1,
        }
        headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}'
        }
        response = self.client.post(uri, data=data, headers=headers, content_type='application/json')
        logger.debug('mission evaluation failure result: ' + str(response.content))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('image_check_passed'), False)
        logger.debug('mission evaluation failure result: ' + str(response.content))