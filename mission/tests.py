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
TEMP_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT, DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class TestMission(TestCase):
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

    def test_mission_random_create_api(self):
        """
        사진이 없는 장소(place)에 대해 임의 미션을 생성하는 POST API 테스트입니다.
        """
        url = '/mission/random/'

        headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}',
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

    def test_object_detection_success_with_peace_photo(self):
        user = User.objects.get(username="TestUser")

        travel = Travel.objects.create(tour_name="테스트 여행", start_date="2024-01-01", end_date="2024-01-02")
        travel.user.set([user])

        mission = Mission.objects.get(content="손 하트 만든 상태로 사진찍기")

        place = Place.objects.create(name="테스트 장소", mapX=127.001, mapY=37.501)
        tdp = TravelDaysAndPlaces.objects.create(travel=travel, place=place, date="2024-01-01", mission=mission)

        # 테스트 이미지 복사 경로 설정
        src_path = "tests/media/peace_sample.jpg"
        dst_path = "tests/media/test_uploaded_peace.jpg"
        shutil.copy(src_path, dst_path)  # 복사

        with open(dst_path, "rb") as f:
            tdp.mission_image.save("peace_photo.png", File(f))

        # 이제 파일 경로 직접 넘김
        detector = ObjectDetection()
        result = detector.detect_and_check(dst_path, mission.content)
        self.assertTrue(result)

    def test_object_detection_fail_with_wrong_image(self):
        """
        객체 인식 실패 케이스: 엉뚱한 이미지로 탐지 실패
        """
        user = User.objects.get(username="TestUser")

        travel = Travel.objects.create(tour_name="실패 케이스", start_date="2024-01-01", end_date="2024-01-02")
        travel.user.set([user])

        mission = Mission.objects.get(content="손 하트 만든 상태로 사진찍기")

        place = Place.objects.create(name="엉뚱한 장소", mapX=127.001, mapY=37.501)
        tdp = TravelDaysAndPlaces.objects.create(travel=travel, place=place, date="2024-01-01", mission=mission)

        # 엉뚱한 이미지 복사 경로 설정
        src_path = "tests/media/kawawi_ytk.jpg"
        dst_path = "tests/media/test_uploaded_wrong.jpg"
        shutil.copy(src_path, dst_path)

        with open(dst_path, "rb") as f:
            tdp.mission_image.save("wrong_photo.jpg", File(f))

        detector = ObjectDetection()
        result = detector.detect_and_check(dst_path, mission.content)
        self.assertFalse(result)

    def test_mission_fail_due_to_far_gps_distance(self):
        """
        GPS 거리 초과 실패 케이스 (>200m)
        """
        user = User.objects.get(username="TestUser")

        travel = Travel.objects.create(tour_name="거리 초과 테스트", start_date="2024-01-01", end_date="2024-01-02")
        travel.user.set([user])

        mission = Mission.objects.get(content="손 하트 만든 상태로 사진찍기")

        place = Place.objects.create(name="멀리 있는 장소", mapX=129.0, mapY=39.0)
        tdp = TravelDaysAndPlaces.objects.create(travel=travel, place=place, date="2024-01-01", mission=mission)

        with open("tests/media/peace_sample.jpg", "rb") as f:
            tdp.mission_image.save("peace_photo.png", File(f), save=True)

        user_lat, user_lng = 37.501, 127.001  # 사용자 위치
        distance = NearEventInfo.haversine(user_lat, user_lng, place.mapY, place.mapX)

        self.assertGreater(distance, 200.0)

    def test_mission_check_complete_object_detection_success(self):
        """
        객체 인식 기반 미션 성공 테스트 (유효 GPS + 객체 탐지 통과)
        """
        user = User.objects.get(username="TestUser")

        # 여행 및 미션, 장소 생성
        travel = Travel.objects.create(
            tour_name="객체 인식 성공 테스트",
            start_date="2024-01-01",
            end_date="2024-01-02"
        )
        travel.user.set([user])

        mission = Mission.objects.get(content="손 하트 만든 상태로 사진찍기")
        place = Place.objects.create(name="객체 인식 장소", mapX=127.001, mapY=37.501)

        tdp = TravelDaysAndPlaces.objects.create(
            travel=travel,
            place=place,
            date="2024-01-01",
            mission=mission
        )

        # 이미지 저장: 파일이 존재하고 실제로 저장되도록 명시적으로 save
        with open("tests/media/peace_sample.jpg", "rb") as f:
            tdp.mission_image.save("peace_photo.jpg", File(f))
            tdp.save()  # 명시적으로 다시 저장

        # API 요청
        url = "/mission/check_complete/"
        headers = {
            'Authorization': f'Bearer {settings.KAKAO_TEST_ACCESS_TOKEN}',
        }
        data = {
            "travel_id": travel.id,
            "place_id": place.id,
            "mission_id": mission.id,
            "mapX": 127.001,
            "mapY": 37.501
        }

        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
            headers=headers
        )

        # 응답 확인
        self.assertEqual(response.status_code, 200)
        res_json = response.json()

        self.assertEqual(res_json["result"], "success")
        self.assertTrue(res_json["location_check_passed"])
        self.assertTrue(res_json["image_check_passed"])
        self.assertEqual(res_json["method_used"], "object_detection")

        # 중복 요청 확인
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json',
            headers=headers
        )

        # 기존 검증
        self.assertEqual(response.status_code, 200)