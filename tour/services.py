import requests
import json


class GeocoderService:
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

        response = self.__get_geocoder_response(
            service='address',
            request='getaddress',
            point=f'{x},{y}',
            format='json',
            type='PARCEL',
            key=self.service_key,
        )
        return response['result']['item']['text']

    def __get_geocoder_response(self, **kwargs) -> json:
        """
        geocoder api의 응답을 받아오는 함수입니다.
        """
        end_point = 'https://api.vworld.kr/req/address'
        response = requests.get(end_point, params=kwargs)
        if response.status_code != 200:
            raise Exception('Geocoder API Error')

        return response.json()


if __name__ == '__main__':
    place = GeocoderService('088ECB86-CAA5-3EF6-8CE0-FB640E00F20E')
    address = place.get_parcel(x=129.053822, y=35.25138)
    print(address)