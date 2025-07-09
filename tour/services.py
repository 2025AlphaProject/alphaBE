import requests
import json

from requests import RequestException

from config.settings import KAKAO_REST_API_KEY, APP_LOGGER, GEOCODER_API_KEY
import logging
from services import tour_api

logger = logging.getLogger(APP_LOGGER)


class PlaceService:
    """
    장소와 관련된 여러 서비스를 구현 합니다.
    """
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

