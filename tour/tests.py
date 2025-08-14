import logging
from unittest.mock import patch
from urllib.parse import urlencode

from channels.testing import WebsocketCommunicator
from django.test import override_settings
from django.urls import reverse

from config.settings import APP_LOGGER
from config.settings import PUBLIC_DATA_PORTAL_API_KEY  # 공공 데이터 포탈 앱 키
from services.tour_api import (
    TourApi,
    MobileOS,
    AreaCode,
    Arrange,
    Category1Code,
    ContentTypeId,
)
from tests.base import BaseTestCase
from tour.consumers import TaskConsumer
from usr.models import User
from .models import Travel, Place

logger = logging.getLogger(APP_LOGGER)


# Create your tests here.

class TestTour(BaseTestCase):
    def setUp(self):
        self.headers = {
            'Authorization': f'Bearer {self.KAKAO_TEST_ACCESS_TOKEN}',
        }
        # 테스트 위한 장소 생성
        self.place = Place.objects.create(
            name='명원박물관',
            mapX='126.9999927956',
            mapY='37.6111883307',
        )
        self.data = {
            "tour_name": "태근이의 여행",
            "tour_date": "2025-07-07",
            "places": {
                "place_ids": [self.place.id],
                "additional_info": [
                    {
                        "place_id": self.place.id,
                        "road_address": "테스트지롱",
                        "place_image": "http://naver.com"
                    }
                ],
                "custom_places": [
                    {
                        "name": "아산 공세리성당",
                        "mapX": "126.9134070332",
                        "mapY": "36.8833377411",
                        "road_address": "충청남도 아산시 인주면 공세리성당길 10"
                    },
                    {
                        "name": "성북구립미술관",
                        "mapX": "126.9949020554",
                        "mapY": "37.594890134",
                        "road_address": "서울특별시 성북구 성북로 134 (성북동)"
                    },
                ]
            }

        }

        # 유저 정보 임의 생성 - 친구 추가를 위한 추가 유저
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

    def test_tour_create_success(self):
        """
            해당 테스트는 여행이 제대로 잘 만들어지는지 확인하는 테스트입니다.
        """
        uri = reverse('create-tour')

        # create test
        response = self.client.post(uri, self.data, headers=self.headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        # self.assertEqual(Place.objects.count(), 3)
        logger.debug('tour create test result: ' + str(response.json()))

    def test_tour_get_list_success(self):
        """
            해당 테스트는 여행 등록 api의 GET 메소드가 제대로 실행되는지 확인하는 테스트입니다.
        """
        uri = reverse('create-tour')
        response = self.client.get(uri, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        logger.debug('tour get list test result: ' + str(response.json()))

    def test_tour_get_detail_success(self):
        """
            해당 테스트는 여행 등록 api의 GET (상세보기, retrieve) 메소드가 제대로 실행되는지 확인하는 테스트입니다.
        """
        self.test_tour_create_success()
        uri = reverse('travel-detail', kwargs={'pk': Travel.objects.first().pk})
        response = self.client.get(uri, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        logger.debug('tour get detail test result: ' + str(response.json()))

    def test_tour_delete_success(self):
        """
            해당 테스트는 여행이 정상적으로 삭제 되는지 확인하기 위한 테스트입니다.
        """
        self.test_tour_create_success() # 여행 생성
        uri = reverse('travel-detail', kwargs={'pk': Travel.objects.first().pk})
        response = self.client.delete(uri, headers=self.headers)
        self.assertEqual(response.status_code, 204)

    def test_tour_delete_fail(self):
        """
            해당 테스트는 없는 여행 번호를 삭제하고자 할 떄 확인하는 테스트입니다.
        """
        uri = reverse('travel-detail', kwargs={'pk': '123141'})
        response = self.client.delete(uri, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        logger.debug('tour delete fail test result: ' + str(response.json()))

    def test_tour_exception_test(self):
        """
            해당 테스트는 정확한 오류코드가 발생되는지 검사하기 위한 테스트입니다.
        """
        # No Required Parameter Exception
        uri = reverse('create-tour')
        exception_data = {
            'id': 1,
            'start_date': '2025-0310',
        }
        response = self.client.post(uri, exception_data, headers=self.headers, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        logger.debug('tour No Required Exception test result: ' + str(response.json()))

        serializer_exception_data = self.data.copy()
        serializer_exception_data.pop('tour_date')
        response = self.client.post(uri, serializer_exception_data, headers=self.headers, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        logger.debug('tour Serializer Exception test result: ' + str(response.json()))

    def test_tour_update_success(self):
        """
            해당 테스트는 여행이 정상적으로 수정이 되는지 확인하기 위한 테스트입니다.
        """
        self.place = Place.objects.create(
            name='명원박물관2',
            mapX='126',
            mapY='37',
        )
        self.data = {
            "tour_name": "태근이의 여행",
            "tour_date": "2025-07-07",
            "places": {
                "place_ids": [self.place.id],
                "additional_info": [
                    {
                        "place_id": self.place.id,
                        "road_address": "테스트지롱2",
                        "place_image": "http://naver.com"
                    }
                ],
                "custom_places": [
                    {
                        "name": "아산 공세리성당",
                        "mapX": "126.9134070332",
                        "mapY": "36.8833377411",
                        "road_address": "충청남도 아산시 인주면 공세리성당길 10"
                    },
                    {
                        "name": "성북구립미술관",
                        "mapX": "126.9949020554",
                        "mapY": "37.594890134",
                        "road_address": "서울특별시 성북구 성북로 134 (성북동)"
                    },
                ]
            }

        }
        self.test_tour_create_success()
        uri = reverse('travel-detail', kwargs={'pk': Travel.objects.first().pk})
        patch_data = {
            'tour_name': '시연이의 여행',
            'tour_date': '2025-07-08',
            'places': {
                'delete_places': [self.place.id]
            }
        }
        response = self.client.patch(uri, patch_data, headers=self.headers, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        logger.debug('tour Update success test result: ' + str(response.json()))

    def test_tour_update_fail(self):
        """
            해당 테스트는 여행이 수정이 되지 못할 때 즉, 여행 장소 정보가 없을 때 발생하는 오류를 테스트합니다.
        """
        self.test_tour_create_success() # 여행 생성
        uri = reverse('travel-detail', kwargs={'pk': Travel.objects.first().pk})
        patch_data = {
            'places': {
                'delete_places': [1123124]
            }
        }
        response = self.client.patch(uri, patch_data, headers=self.headers, content_type='application/json')
        self.assertEqual(response.status_code, 404)
        logger.debug('tour Update fail test result: ' + str(response.json()))

    def test_add_traveler_success(self):
        """
            해당 테스트는 한 여행에 친구 추가가 제대로 되는지 테스트 합니다.
        """
        self.test_tour_create_success() # 여행 추가
        uri = reverse('add_traveler')
        data = {
            'add_traveler_sub': User.objects.first().sub,
            'travel_id': Travel.objects.first().id,
        }
        response = self.client.post(uri, data, headers=self.headers, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        logger.debug('tour Add Traveler success test result: ' + str(response.json()))

    def test_add_traveler_fail(self):
        """
            해당 테스트는 한 여행에 친구 추가가 제대로 안되었을 때 제대로 된 에러 코드가 날라오는지 테스트합니다.
        """
        uri = reverse('add_traveler')
        data = {
            'add_traveler_sub': 1,
            'travel_id': 1,
        }
        strange_data = {
            'aadd_traveler_sub': 1,
            'travel_id': 1,
        }
        response = self.client.post(uri, strange_data, headers=self.headers, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        logger.debug('tour Add Traveler No Required Parameter test result: ' + str(response.json()))

        data['add_traveler_sub'] = 324 # 없는 데이터
        response = self.client.post(uri, data, headers=self.headers, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        logger.debug('tour Add Traveler fail test result: ' + str(response.json()))

    def test_get_area_list_success(self):
        """
        해당 테스트는 시군구 코드를 정확하게 가져오는지 테스트합니다.
        """
        # 200 Test
        end_point = '/tour/get_area_list/?area_code=1'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)

        # sido_list Test
        end_point = '/tour/get_sido_list/'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 200)

    def test_get_sido_list_fail(self):
        """
            해당 테스트는 시군구 코드 가져오는 것을 실패했을 때를 테스트합니다.
        """
        #404 Test
        end_point = '/tour/get_area_list/?area_code=234'
        response = self.client.get(end_point)
        self.assertEqual(response.status_code, 404)

    # tour/consumers.py에 있는 app.send_task 함수를 Mock() 객체로 교체
    # Mock 객체를 테스트 함수 인자로 넘김
    @patch('tour.consumers.app.send_task')
    @override_settings(CHANNEL_LAYERS={
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer"
        }
    },
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'test-cache'
            }
        }
    )
    async def test_tour_recommender(self, mock_send_task):
        """
            해당 테스트는 웹소켓 통신을 테스트합니다.
        """
        mock_send_task.return_value.task_id = 'mocked-task-id'
        params = {
            'areaCode': '34',
            'user_id': '111',
            'unique_code': '1',
            'sigunguName': '아산',
            'categoryName': '39',
        }
        query_string = urlencode(params)
        communicator = WebsocketCommunicator(
            TaskConsumer.as_asgi(),
            f'/tour/recommend/?{query_string}',
        )
        connected, subprotocol = await communicator.connect(20)
        self.assertTrue(connected)
        response = await communicator.receive_json_from(10)
        logger.debug('tour Recommender test result: ' + str(response))
        ans = response.get('state') == 'OK' or response.json().get('state') == 'CACHE_HIT'
        self.assertTrue(ans)

    def testSnapshot_post_success(self):
        """
            인생네컷 사진 업로드 성공 테스트
        """
        pass

    def testSnapshot_post_fail(self):
        """
            인생네컷 사진 업로드 실패 테스트
        """
        pass

    def testSnapshot_list_success(self):
        """
            인생네컷 사진 리스트 가져오기 성공 테스트
        """
        pass

    def testSnapshot_list_fail(self):
        """
            인생네컷 사진 리스트 가져오기 실패 테스트
        """
        pass

    def testSnapshot_retrieve_success(self):
        """
            인생네컷 사진 상세 가져오기 성공 테스트
        """
        pass

    def testSnapshot_retrieve_fail(self):
        """
            인생네컷 사진 상세 가져오기 실패 테스트
        """
        pass

    def test_tour_image_post_success(self):
        """
            여행 사진 업로드 성공 테스트
        """
        pass

    def test_pose_recommend_retrieve_for_no_cat_success(self):
        """
            카테고리가 없는 장소에 대한 포즈 추천 성공 테스트
        """
        # 장소가 존재하지 않을 경우를 대비해 장소를 만듭니다.
        place = Place.objects.create(
            name='명원박물관 테스트',
            mapX='127',
            mapY='37.8111883307',
        )
        uri = f'{reverse('pose_recommend')}?place_id={place.id}'
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        logger.debug('tour Recommend for no cat test result: ' + str(response.json()))

    def test_pose_recommend_retrieve_for_cat_success(self):
        """
            카테고리가 존재하는 장소에 대한 포즈 추천 성공 테스트
        """
        # 장소가 존재하지 않을 경우를 대비해 장소를 만듭니다.
        place = Place.objects.create(
            name='명원박물관 테스트',
            mapX='127',
            mapY='37.8111883307',
            cat2='B0201'
        )
        uri = f'{reverse('pose_recommend')}?place_id={place.id}'
        response = self.client.get(uri)
        self.assertEqual(response.status_code, 200)
        logger.debug('tour Recommend for cat test result: ' + str(response.json()))



