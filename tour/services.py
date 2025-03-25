import requests
import json
from config.settings import KAKAO_REST_API_KEY, APP_LOGGER
import logging

logger = logging.getLogger(APP_LOGGER)


class PlaceService:
    """
    장소와 관련된 여러 서비스를 구현 합니다.
    """
    def __init__(self, service_key=None):
        self.service_key = service_key

    def get_parcel(self, x: float, y: float):
        """
        해당 함수는 위도 경도 좌표에 해당하는 지번 주소를 반환하는 함수 입니다.
        """
        if not self.service_key:
            raise Exception('Service Key is required')

        response = self.__get_kakao_response(x=x, y=y)
        parcel_address = response['documents'][0]['address']['address_name']
        if parcel_address is None:
            logger.warning('There is no address')
            return ""
        return parcel_address

    def __get_kakao_response(self, **kwargs) -> json:
        """
        kakao api의 응답을 받아오는 함수입니다.
        """
        end_point = 'https://dapi.kakao.com/v2/local/geo/coord2address.JSON'
        headers = {'Authorization': f'KakaoAK {self.service_key}'}
        response = requests.get(end_point, params=kwargs, headers=headers)
        if response.status_code != 200:
            logger.error('kakao local api error (38)')
            raise Exception('Kakao API Error')

        return response.json()
