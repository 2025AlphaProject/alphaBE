from django.test import TestCase
from config.settings import PUBLIC_DATA_PORTAL_API_KEY, KAKAO_TEST_ACCESS_TOKEN  # 공공 데이터 포탈 앱 키
from .modules.tour_api import (
    TourApi,
    MobileOS,
    AreaCode,
    Arrange,
    Category1Code,
    ContentTypeId,
)
from usr.models import User
from .models import Travel

# Create your tests here.

class TestTour(TestCase):
    def setUp(self):
        # 유저 정보 임의 생성
        user = User.objects.create(
            sub=3935716527,
            username='TestUser',
            gender='male',
            age_range='1-9',
            profile_image_url='https://example.org'
        )
        user.set_password('test_password112')
        user.save()

        # 유저 정보 임의 생성2
        user2 = User.objects.create(
            sub=1,
            username='TestUser2',
            gender='male',
            age_range='1-9',
            profile_image_url='https://example.org'
        )
        user2.set_password('test_password112')
        user2.save()
    def test_tour_api_module(self):
        """
        해당 테스트는 module/tour_api를 테스트하기 위해 작성된 테스트 코드 입니다.
        """
        tour = TourApi(MobileOS=MobileOS.ANDROID, MobileApp='AlphaTest')
        tour.set_serviceKey(PUBLIC_DATA_PORTAL_API_KEY)
        # 지역 기반 관광지 가져오기 1
        area = tour.get_area_based_list(areaCode=AreaCode.SEOUL,
                                        sigunguCode=tour.get_sigungu_code(areaCode=AreaCode.SEOUL, targetName='성북'))
        self.assertNotEqual(area, None)

        # 지역 기반 관광지 가져오기 2
        data = {
            'areaCode': AreaCode.SEOUL,
            'sigunguCode': tour.get_sigungu_code(areaCode=AreaCode.SEOUL, targetName='종로'),
            'arrange': Arrange.TITLE_IMAGE,
            'contentTypeId': ContentTypeId.GWANGWANGJI
        }
        area = tour.get_area_based_list(**data)
        self.assertNotEqual(area, None)

        # 카테고리 코드 가져오기 테스트
        categories = tour.get_category_code_list(cat1=Category1Code.HUMANITIES, cat2='A0201')
        self.assertNotEqual(categories, None)

        # 위치 기반 관광지 가져오기
        data = {
            'areaCode': AreaCode.SEOUL,
            'arrange': Arrange.TITLE_IMAGE,
            'contentTypeId': ContentTypeId.GWANGWANGJI
        }
        response = tour.get_location_based_list(126.3547412438, 34.4354594945, 20000)
        self.assertNotEqual(response, None)

        # 행사 정보 가져오기
        data.pop('contentTypeId')
        response = tour.get_festival_list('20250315', '20250318', **data)
        self.assertNotEqual(response, None)
        # for each in response:
        #     print(each.get_eventStartDate(), each.get_eventEndDate())

    def test_travel_api(self):
        uri = '/tour/'
        headers = {
            'Authorization': f'Bearer {KAKAO_TEST_ACCESS_TOKEN}',
        }
        data = {
            'tour_name': '태근이의 여행',
            'start_date': '2025-03-10',
            'end_date': '2025-03-15',
        }
        # 빈 데이터 list get Test
        response = self.client.get(uri, headers=headers)
        self.assertEqual(response.status_code, 200)

        # create test
        response = self.client.post(uri, data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # 인스턴스 임의로 하나 더 생성
        data['tour_name'] = '태근이의 여행2'
        response = self.client.post(uri, data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # list get Test
        response = self.client.get(uri, headers=headers)
        self.assertEqual(response.status_code, 200)

        # detail get Test
        id = Travel.objects.get(tour_name='태근이의 여행').id
        uri_detail = f'/tour/{id}/' # 아이디 1번
        response = self.client.get(uri_detail, headers=headers)
        self.assertEqual(response.status_code, 200)

        # delete Test
        response = self.client.delete(uri_detail, headers=headers)
        self.assertEqual(response.status_code, 204)
        response = self.client.get(uri, headers=headers)
        self.assertEqual(response.status_code, 200)

        # put Test - Exception Test
        put_data = {
            'tour_name': '시연이의 여행'
        }
        response = self.client.put(uri_detail, put_data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 404)

        # put Test
        id2 = Travel.objects.get(tour_name='태근이의 여행2').id
        uri_detail = f'/tour/{id2}/'  # 아이디 2번
        response = self.client.put(uri_detail, put_data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 200)

        # get Test - Exception Test
        uri_detail = f'/tour/{id}/'
        response = self.client.get(uri_detail, headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_add_traveler(self):
        end_point = '/tour/'
        headers = {
            'Authorization': f'Bearer {KAKAO_TEST_ACCESS_TOKEN}',
        }
        data = {
            'tour_name': '태근이의 여행',
            'start_date': '2025-03-10',
            'end_date': '2025-03-15',
        }
        response = self.client.post(end_point, headers=headers, data=data, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        end_point = '/tour/add_traveler/'
        data = {
            'add_traveler_sub': 1,
            'travel_id': 1,
        }
        # Normal POST Test
        response = self.client.post(end_point, data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Exception Test
        strange_data = {
            'aadd_traveler_sub': 1,
            'travel_id': 1,
        }
        response = self.client.post(end_point, strange_data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 400)

        data['add_traveler_sub'] = 324 # 없는 데이터
        response = self.client.post(end_point, data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_get_area_list(self):
        """
        해당 테스트는 시군구 코드를 정확하게 가져오는지 테스트합니다.
        """
        # 200 Test
        end_point = '/tour/get_area_list/?area_code=1'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)

        #404 Test
        end_point = '/tour/get_area_list/?area_code=234'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 404)

        # sido_list Test
        end_point = '/tour/get_sido_list/'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)

    def test_save_course(self):
        """
        해당 테스트는 /tour/course/ 경로 저장 API가 정상적으로 작동하는지 검증합니다.
        """

        # 1️⃣ 여행 생성
        headers = {
            'Authorization': f'Bearer {KAKAO_TEST_ACCESS_TOKEN}',
        }
        travel_data = {
            'tour_name': '테스트 여행',
            'start_date': '2025-04-01',
            'end_date': '2025-04-05'
        }
        create_response = self.client.post('/tour/', data=travel_data, headers=headers, content_type='application/json')
        self.assertEqual(create_response.status_code, 201)
        tour_id = create_response.json()['tour_id']

        # 2️⃣ 정상적인 코스 저장 요청
        course_data = {
            "tour_id": tour_id,
            "date": "2025-04-02",
            "places": [
                {
                    "name": "광화문",
                    "mapX": "126.9769",
                    "mapY": "37.5759",
                    "image_url": "https://image.example.com/gwanghwamun.jpg"
                },
                {
                    "name": "서울역",
                    "mapX": "126.9706",
                    "mapY": "37.5562",
                    "image_url": "https://image.example.com/seoul.jpg"
                }
            ]
        }
        response = self.client.post('/tour/course/', data=course_data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)  # ✅ 정상적으로 저장되었는지 확인
        self.assertEqual(response.json()['date'], "2025-04-02")
        self.assertEqual(len(response.json()['places']), 2)

        # 3️⃣ 예외 케이스: 필수 필드 누락 (date 없음)
        bad_data = {
            "tour_id": tour_id,
            "places": [
                {
                    "name": "남산타워",
                    "mapX": "126.9882",
                    "mapY": "37.5512",
                    "image_url": "https://image.example.com/namsan.jpg"
                }
            ]
        }
        response = self.client.post('/tour/course/', data=bad_data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 400)

        # 4️⃣ 예외 케이스: 존재하지 않는 여행 ID
        wrong_data = {
            "tour_id": 9999,
            "date": "2025-04-03",
            "places": [
                {
                    "name": "북촌한옥마을",
                    "mapX": "126.9870",
                    "mapY": "37.5825",
                    "image_url": "https://image.example.com/bukchon.jpg"
                }
            ]
        }
        response = self.client.post('/tour/course/', data=wrong_data, headers=headers, content_type='application/json')
        self.assertEqual(response.status_code, 403)