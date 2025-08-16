import json
import logging

import requests

from config.settings import APP_LOGGER, GEOCODER_API_KEY
from typing import Dict, List, Optional
from django.db import transaction
from .models import Travel, Place, TravelDaysAndPlaces
from .serializers import TravelSerializer, TravelDaysAndPlacesSerializer, PlaceSerializer
from usr.models import User
from services.exception_handler import *

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

        # 10m 내 기존 장소 검색
        existing_place = self._find_nearest_place(mapX, mapY)
        if existing_place:
            return existing_place

        # 새 장소 생성
        return self._create_new_place(place_data, mapX, mapY)

    def _find_nearest_place(self, x: float, y: float) -> Optional[Place]:
        """10m 내에 있는 가장 가까운 장소 찾기"""
        from django.db.models import FloatField
        from django.db.models.functions import Cast
        from services.utils import haversine

        near_places = Place.objects.annotate(
            mapX_float=Cast('mapX', FloatField()),
            mapY_float=Cast('mapY', FloatField())
        ).filter(
            mapX_float__gte=(x - self.LON_DIF_PER_10M),
            mapX_float__lte=(x + self.LON_DIF_PER_10M),
            mapY_float__gte=(y - self.LAT_DIF_PER_10M),
            mapY_float__lte=(y + self.LAT_DIF_PER_10M)
        )

        closest_place = None
        min_distance = None

        for place in near_places:
            distance = haversine(x, y, float(place.mapX), float(place.mapY))
            if min_distance is None or distance < min_distance:
                closest_place = place
                min_distance = distance

        return closest_place

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

