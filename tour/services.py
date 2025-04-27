import requests
import json
from config.settings import KAKAO_REST_API_KEY, APP_LOGGER
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
            logger.error('kakao local api error (38)')
            raise Exception('Kakao API Error')

        return response.json()

