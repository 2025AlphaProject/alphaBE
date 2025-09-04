import json
import logging

import requests

from config.settings import APP_LOGGER, GEOCODER_API_KEY, PUBLIC_DATA_PORTAL_API_KEY
from typing import Dict, List, Optional
from django.db import transaction
from .models import Travel, Place, TravelDaysAndPlaces, SnapshotImages, UserTourImage
from .serializers import TravelSerializer, TravelDaysAndPlacesSerializer, PlaceSerializer, TodayTravelSerializer
from usr.models import User
from services.exception_handler import *
from django.utils import timezone
from services.tour_api_service import TourAPIService, area_codes
from tour.sigungu import SIGUNGU_DATA
import difflib
from services.utils import haversine

logger = logging.getLogger(APP_LOGGER)


class PlaceService:
    """
    장소와 관련된 여러 서비스를 구현 합니다.
    """
    metadata = None
    def __init__(self, service_key=None):
        self.service_key = service_key

    def get_parcel_and_road_address(self, x: float, y: float) -> tuple[str, str]:
        """
        해당 함수는 지번 주소와 도로명 주소를 모두 얻어내는 함수입니다.
        :return: (parcel_address, road_address)
        """
        if not self.service_key:
            raise Exception('Service Key is required')

        response = self.__get_kakao_address_response(x=x, y=y)
        if response is None: # 만약에 한도 초과가 발생했다면
            response = self.__get_geocoder_response(x=x, y=y)
            if response['status'] != 'OK':
                logger.warning(response['message'])
                return "", ""
            parcel = response['result'][0].get('text', '')
            if len(response['result']) == 1:
                return parcel, ""
            road = response['result'][1].get('text', '')
            return parcel, road


        if response['meta']['total_count'] == 0: # 정보가 아예 존재하지 않을 때
            logger.warning(f'There is no address (x: {x}, y: {y})')
            return "", ""

        result_data = response['documents'][0]
        parcel_address = result_data.get('address', None)
        if parcel_address is not None:
            parcel_address = parcel_address.get('address_name', None)
        road_address = result_data.get('road_address', None)
        if road_address is not None:
            road_address = road_address.get('address_name', None)

        if parcel_address is None:
            logger.warning(f'There is no parcel address (x: {x}, y: {y})')
            parcel_address = ""
        if road_address is None:
            logger.warning(f'There is no road address (x: {x}, y: {y})')
            road_address = ""
        return parcel_address, road_address



    def get_parcel(self, x: float, y: float) -> str:
        """
        해당 함수는 위도 경도 좌표에 해당하는 지번 주소를 반환하는 함수 입니다.
        """
        return self.get_parcel_and_road_address(x, y)[0]

    def get_road_address(self, x: float, y: float) -> str:
        """
        해당 함수는 위도 경도 좌표에 해당하는 도로명 주소를 반환하는 함수입니다.
        """
        return self.get_parcel_and_road_address(x, y)[1]

    def __get_kakao_address_response(self, **kwargs) -> json:
        """
        kakao api의 좌표-주소 응답을 받아오는 함수입니다.
        """
        end_point = 'https://dapi.kakao.com/v2/local/geo/coord2address.JSON'
        headers = {'Authorization': f'KakaoAK {self.service_key}'}
        response = requests.get(end_point, params=kwargs, headers=headers)
        if response.status_code != 200:
            logger.error(response.text)
            return None

        return response.json()

    def __get_geocoder_response(self, **kwargs):
        end_point = "https://api.vworld.kr/req/address"
        params = {
            "service": "address",
            "request": "getAddress",
            "point": f"{kwargs['x']},{kwargs['y']}",
            "type": "BOTH",
            "key": GEOCODER_API_KEY,
            "simple": "true"
        }
        response = requests.get(end_point, params=params)
        if response.status_code != 200:
            logger.error(response.text)
            if response.status_code == 502: # bad gateway인 경우 즉, CI 환경에서는 아래 mockup으로 동작
                return {'service': {'name': 'address', 'version': '2.0', 'operation': 'getAddress', 'time': '11(ms)'}, 'status': 'OK', 'result': [{'zipcode': '03045', 'text': '서울특별시 종로구 세종로 1-58', 'structure': {'level0': '대한민국', 'level1': '서울특별시', 'level2': '종로구', 'level3': '', 'level4L': '세종로', 'level4LC': '1111011900', 'level4A': '청운효자동', 'level4AC': '1111051500', 'level5': '1-58도', 'detail': ''}}, {'zipcode': '03045', 'text': '서울특별시 종로구 사직로 161 (세종로,경복궁)', 'structure': {'level0': '대한민국', 'level1': '서울특별시', 'level2': '종로구', 'level3': '세종로', 'level4L': '사직로', 'level4LC': '3100005', 'level4A': '청운효자동', 'level4AC': '1111051500', 'level5': '161', 'detail': '경복궁'}}]}
            raise Exception('Geocoder API Error')
        return response.json()['response']


class TravelCreationService:
    """
        여행 생성과 관련된 모든 로직을 담당하는 서비스 입니다.
    """

    def __init__(self, place_service: PlaceService):
        self.place_service = place_service # 클래스 내에 하나의 객체만 사용토록 하여 여러 메서드에 공유하여 사용합니다.
        self.LON_DIF_PER_10M = 0.00547202  # 경도 차이 (10m)
        self.LAT_DIF_PER_10M = 0.00009  # 위도 차이 (10m)

    @transaction.atomic
    def create_travel_with_places(self, travel_data: Dict, places_data: Dict, user_sub: int) -> Travel:
        """
            여행과 장소를 잇는 tdp를 생성하는 로직입니다.
        """
        # 1. 여행 생성
        travel = self._create_travel(travel_data, user_sub)

        # 2. tdp 생성
        self._process_places(travel.id, places_data)

        return travel

    @staticmethod
    def _create_travel(travel_data: Dict, user_sub: int) -> Travel:
        """여행 객체 생성"""
        serializer = TravelSerializer(data=travel_data)
        serializer.is_valid(raise_exception=True)
        travel = serializer.save()
        travel.user.add(User.objects.get(sub=user_sub))
        return travel

    def _process_places(self, travel_id: int, places_data: Dict) -> None:
        """장소 데이터 처리 (기존 장소, 추가 정보, 커스텀 장소)"""
        # 각 데이터를 분리하여 각 데이터에 맞는 핸들러에 전달하여 처리합니다.
        place_handlers = [
            (places_data.get('place_ids'), self._handle_existing_places),
            (places_data.get('additional_info'), self._handle_additional_info),
            (places_data.get('custom_places'), self._handle_custom_places)
        ]

        for data, handler in place_handlers:
            if data:
                handler(travel_id, data)

    def _handle_existing_places(self, travel_id: int, place_ids: List[int]) -> None:
        """기존 DB에 있던 장소들 처리"""
        for place_id in place_ids:
            # 여행-장소 관계 생성
            self._create_travel_place_relation(travel_id, place_id)

            # 주소 정보 업데이트
            place = Place.objects.get(pk=place_id)
            self._update_place_address(place)

    @staticmethod
    def _handle_additional_info(travel_id: int, additional_info: List[Dict]) -> None:
        """기존 DB 장소들의 추가 정보 업데이트"""
        for info in additional_info:
            place_id: Optional[int] = info.pop('place_id', None) # place_id를 정적 분석에 실패하여 if문 아래로 도달하지 못한다 판단하여 타입 힌트로 해결
            if not place_id:
                raise NoRequiredParameterException(error_message='place_id 누락')

            try:
                place = Place.objects.get(id=int(place_id))
            except Place.DoesNotExist:
                raise NoObjectException(error_code='NotFoundInAddIn')

            # 장소 정보 업데이트
            serializer = PlaceSerializer(instance=place, data=info, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def _handle_custom_places(self, travel_id: int, custom_places: List[Dict]) -> None:
        """사용자 추가 장소들 처리"""
        for place_data in custom_places:
            mapX = place_data.get('mapX')
            mapY = place_data.get('mapY')

            if not mapX or not mapY:
                raise NoRequiredParameterException()

            # 근처 장소 검색 또는 새로 생성
            place = self._get_or_create_place(place_data)

            # 중복 체크 후 관계 생성
            self._create_travel_place_relation_if_not_exists(travel_id, place.id)

    def _get_or_create_place(self, place_data: Dict) -> Place:
        """근처 장소 검색 또는 새로운 장소 생성"""
        mapX, mapY = float(place_data['mapX']), float(place_data['mapY'])
        name = place_data.get('name')
        if name is None: NoRequiredParameterException()

        # 이름이 일치하고, 그 일치하는 장소들 중에서 1km 내에 있는 장소 정보를 가져옵니다.
        place = self.__get_place_by_name_equal(name, mapX, mapY)
        if place is not None: return place

        # 이름 불일치 시
        # 10m 내 기존 장소 검색
        existing_place = self._find_nearest_place(name, mapX, mapY)
        if existing_place:
            return existing_place

        # 새 장소 생성
        return self._create_new_place(place_data, mapX, mapY)

    def _find_nearest_place(self, original_place_name:str, x: float, y: float) -> Optional[Place]:
        """50m 내에 있는 가장 가까운 장소 찾기"""
        from django.db.models import FloatField
        from django.db.models.functions import Cast

        near_places = Place.objects.annotate(
            mapX_float=Cast('mapX', FloatField()),
            mapY_float=Cast('mapY', FloatField())
        ).filter(
            mapX_float__gte=(x - (self.LON_DIF_PER_10M * 10)),
            mapX_float__lte=(x + (self.LON_DIF_PER_10M * 10)),
            mapY_float__gte=(y - (self.LAT_DIF_PER_10M * 10)),
            mapY_float__lte=(y + (self.LAT_DIF_PER_10M * 10))
        )

        near_places_after_similarity = []
        for place in near_places:
            # 이름 유사도 검사
            if self._check_name_similarity(original_place_name, place.name):
                near_places_after_similarity.append(place)

        if len(near_places_after_similarity) == 1: return near_places_after_similarity.pop() # 하나면 그냥 반환

        closest_place = None
        min_distance = None

        for place in near_places_after_similarity:
            distance = haversine(x, y, float(place.mapX), float(place.mapY))
            if min_distance is None or distance < min_distance:
                closest_place = place
                min_distance = distance


        return closest_place

    def _check_name_similarity(self, name1, name2):
        # 장소 이름 유사도 검사를 실시합니다.
        CUTLINE = 0.8 # 유사도 80% 이상 시 통과
        answer_bytes = bytes(name1, 'utf-8')
        input_bytes = bytes(name2, 'utf-8')
        answer_bytes_list = list(answer_bytes)
        input_bytes_list = list(input_bytes)

        sm = difflib.SequenceMatcher(None, answer_bytes_list, input_bytes_list)
        similar = sm.ratio()
        if similar >= CUTLINE:
            return True
        else:
            return False


    def _create_new_place(self, place_data: Dict, mapX: float, mapY: float) -> Place:
        """새로운 장소 생성"""
        name = place_data.get('name')
        if not name:
            raise NoRequiredParameterException()

        # 주소 정보 가져오기
        road_address_kakao, address_kakao = self.place_service.get_parcel_and_road_address(mapX, mapY)

        return Place.objects.create(
            name=name,
            mapX=str(mapX),
            mapY=str(mapY),
            road_address=place_data.get('road_address', road_address_kakao),
            address=address_kakao,
        )

    @staticmethod
    def _create_travel_place_relation(travel_id: int, place_id: int) -> None:
        """tdp 생성"""
        data = {"place": place_id, "travel": travel_id}
        serializer = TravelDaysAndPlacesSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _create_travel_place_relation_if_not_exists(self, travel_id: int, place_id: int) -> None:
        """중복이 아닌 경우에만 여행-장소 관계 생성"""
        try:
            TravelDaysAndPlaces.objects.get(travel_id=travel_id, place_id=place_id)
        except TravelDaysAndPlaces.DoesNotExist:
            self._create_travel_place_relation(travel_id, place_id)

    def _update_place_address(self, place: Place) -> None:
        """장소의 주소 정보 업데이트"""
        road_address, address = self.place_service.get_parcel_and_road_address(
            float(place.mapX), float(place.mapY)
        )
        serializer = PlaceSerializer(instance=place, data={"address": address}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    @staticmethod
    def __get_place_by_name_equal(name, mapX, mapY):
        db_places = Place.objects.filter(name=name)
        for db_place in db_places:
            if haversine(db_place.mapX, db_place.mapY, mapX, mapY) > 1:  # 1km보다 크다면
                continue
            return db_place
        return None


class TravelUpdateService:
    """여행 업데이트와 관련된 로직을 담당하는 서비스"""

    def __init__(self, creation_service: TravelCreationService):
        self.creation_service = creation_service

    @transaction.atomic
    def update_travel_with_places(self, travel_id: int, travel_data: Dict, places_data: Dict = None) -> Travel:
        """여행 정보와 장소를 함께 업데이트"""
        # 1. 여행 기본 정보 업데이트
        if travel_data:
            self._update_travel_info(travel_id, travel_data)

        # 2. 장소 관련 업데이트
        if places_data:
            self._process_place_updates(travel_id, places_data)

        return Travel.objects.get(id=travel_id)

    def _update_travel_info(self, travel_id: int, travel_data: Dict) -> None:
        """여행 기본 정보 업데이트"""
        travel = Travel.objects.get(id=travel_id)
        serializer = TravelSerializer(travel, data=travel_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def _process_place_updates(self, travel_id: int, places_data: Dict) -> None:
        """장소 관련 업데이트 처리"""
        # 장소 삭제
        delete_places = places_data.get('delete_places')
        if delete_places:
            self._delete_travel_places(travel_id, delete_places)

        # 새로운 장소 추가/업데이트
        self.creation_service._process_places(travel_id, places_data)

    def _delete_travel_places(self, travel_id: int, place_ids: List[int]) -> None:
        """여행에서 장소들 제거"""
        for place_id in place_ids:
            try:
                tdp = TravelDaysAndPlaces.objects.get(travel_id=travel_id, place_id=place_id)
                tdp.delete()
            except TravelDaysAndPlaces.DoesNotExist:
                raise NoObjectException(error_message='해당 여행 장소에 맞는 여행 정보를 찾을 수 없습니다.')

class TodayTravelService:
    def __init__(self):
        self.tour_api_service = TourAPIService(service_key=PUBLIC_DATA_PORTAL_API_KEY)

    def get_today_tour_by_user(self, user):
        """
            유저 정보를 통해 오늘의 여행 정보를 얻습니다.
        """
        response_list = []
        # 모든 당일 여행 정보를 가져옵니다.
        self.__get_today_tour_list_by_user_data(user=user)
        for tour in self.tour_list:
            # 시리얼라이저에 들어갈 데이터를 획득합니다.
            data = self.__get_today_tour_by_user_data(tour=tour)
            response_list.append(data)
        # 시리얼라이저를 통해 필드를 '검증합니다.'
        serializer = self.__validate_field(data=response_list)
        # 검증된 시리얼라이저를 반환합니다.
        return serializer

    def __get_today_tour_list_by_user_data(self, user):
        self.tour_list = Travel.objects.filter(user=user, tour_date=timezone.now())
        if len(self.tour_list) == 0: raise NoObjectException(error_message='오늘의 여행 정보를 찾을 수 없습니다.')

    def __get_today_tour_by_user_data(self, tour):
        # 여행을 인스턴스 객체로 등록합니다.
        self.tour = tour

        # 시리얼라이저에 대응하는 데이터를 핸들러를 통해 가져옵니다.
        serializer_data_handler_list = [
            ('tour_name', self.__get_tour_name),
            ('tour_date', self.__get_tour_date),
            ('people_cnt', self.__get_people_cnt),
            ('image_cnt', self.__get_image_cnt),
            ('place_cnt', self.__get_place_cnt),
            ('category_list', self.__get_category_list),
            ('tour_area_info', self.__get_tour_area_info),
            ('tour_id', self.__get_tour_id)
        ]
        # 핸들러를 실행하여 반환 객체에 담습니다.
        data = dict()

        for target, handler in serializer_data_handler_list:
            data[target] = handler()

        return data

    def __get_tour_id(self):
        return self.tour.id

    def __get_tour_name(self):
        return self.tour.tour_name

    def __get_tour_date(self):
        return self.tour.tour_date

    def __get_people_cnt(self):
        return self.tour.user.count()

    def __get_image_cnt(self):
        return UserTourImage.objects.filter(tour=self.tour).count()

    def __get_place_cnt(self):
        return TravelDaysAndPlaces.objects.filter(travel=self.tour).count()

    def __get_category_list(self):
        # 모든 여행 장소들에 대한 카테고리 정보를 수집합니다.
        category_set = set() # 중복되면 안되므로 set 형식입니다.
        for tdp in TravelDaysAndPlaces.objects.filter(travel=self.tour):
            info = tdp.place.contenttypeid
            if info is not None and info != "":
                category_set.add(int(tdp.place.contenttypeid))
        return sorted(list(category_set)) # 정렬된 리스트를 보냅니다.

    def __get_tour_area_info(self) -> list[str]:
        # 모든 여행 장소들에 대한 지역 정보를 수집합니다.
        # 모든 장소들에 대해 중복없이 지역코드를 추출합니다.
        area_code_list = self.__get_area_code_list_from_places() # ('시/도', '시군구')
        # 해당 지역코드를 tour_api 서비스를 이용해 지역 코드를 가져옵니다.
        area_list_str = self.__convert_area_code_list_to_area_str(area_code_list)
        return area_list_str

    def __get_area_code_list_from_places(self):
        # (17개 시/도, 세부 시군구) 형식으로 데이터를 제공합니다.
        area_code_set = set()
        places = Place.objects.filter(traveldaysandplaces__travel=self.tour)
        for place in places:
            if place.areacode is not None:
                area_code_set.add((place.areacode, place.sigungucode))
        return sorted(list(area_code_set))




    def __convert_area_code_list_to_area_str(self, area_code_list):
        ans_list = []
        for area_code, sigungu_code in area_code_list:
            ans = f'{area_codes.get(str(area_code))} {self.__convert_sigungu_code_to_str(area_code, sigungu_code)}'
            ans_list.append(ans)
        return ans_list

    def __convert_sigungu_code_to_str(self, area_code, sigungu_code):
        sigungus = SIGUNGU_DATA.get(int(area_code))
        for each in sigungus:
            if each.get('code') == str(sigungu_code):
                return each.get('name')
        raise UnExpectedException(error_message='시군구 코드 없음')



    @staticmethod
    def __validate_field(data):
        serializer = TodayTravelSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        return serializer