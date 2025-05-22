import requests

class HttpRequestException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message


class PublicDataPortalHttpClient:
    """
    해당 클래스는 공공 데이터 포탈과 직접 소통하는 http 클라이언트 입니다.
    """
    def __init__(self, service_key):
        # 공공 데이터 포탈과 소통하기 위한 서비스 키입니다.
        self.service_key = service_key

    def get_tour_api_response(self, path: str, **kwargs):
        """
        해당 함수는 한국관광공사_국문 관광정보 서비스_GW api와 직접 소통하는 함수 입니다.
        :param path: 요청을 보낼 path를 의미합니다.
        :param kwargs: 서비스 키를 제외한 요청을 보낼 body를 의미하며 dictionary 형태를 받습니다.
        """
        base_url = 'http://apis.data.go.kr/B551011/KorService2'
        kwargs['serviceKey'] = self.service_key
        response = requests.get(base_url + path, params=kwargs)
        if response.status_code == 200:
            return response.json()
        raise HttpRequestException(f'Public Data Portal API HTTP request failed with status code {response.status_code}')
