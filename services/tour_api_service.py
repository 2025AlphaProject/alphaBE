from dataclasses import dataclass

from config.settings import PUBLIC_DATA_PORTAL_API_KEY
from services.public_data_portal_http_client import HttpRequestException
from .tour_api_http_client import *

area_codes = {
    '1': '서울',
    '2': '인천',
    '3': '대전',
    '4': '대구',
    '5': '광주',
    '6': '부산',
    '7': '울산',
    '8': '세종특별자치시',
    '31': '경기도',
    '32': '강원특별자치도',
    '33': '충청북도',
    '34': '충청남도',
    '35': '경상북도',
    '36': '경상남도',
    '37': '전북특별자치도',
    '38': '전라남도',
    '39': '제주특별자치도'
}

@dataclass
class Place:
    """
    장소 정보를 저장하는 데이터 클래스 입니다.
    """
    addr1: str = None # 상세주소
    addr2: str = None # 지역코드
    areacode: str = None # 대분류코드
    cat1: str = None # 중분류코드
    cat2: str = None # 소분류코드
    cat3: str = None # 상세주소
    contentid: str = None # 콘텐츠ID
    contenttypeid: str = None # 관광타입(관광지, 숙박등) ID
    created_time: str = None # 콘텐츠최초등록일
    firstimage: str = None # 원본대표이미지
    cpyrhtDivCd: str = None # Type1:제1유형(출처표시-권장) Type3:제3유형(제1유형 + 변경금지)
    mapx: str = None # GPS X좌표(WGS84 경도좌표) 응답
    mapy: str = None # GPS Y좌표(WGS84 경도좌표) 응답
    mlevel: str = None # Map Level 응답
    modifiedtime: str = None # 콘텐츠수정일
    sigungucode: str = None # 시군구코드
    tel: str = None # 전화번호
    title: str = None # 콘텐츠제목
    zipcode: str = None # 우편번호
    lDongRegnCd: str = None # 법정동 시도 코드
    lDongSignguCd: str = None # 법정동 시군구 코드
    lclsSystm1: str = None # 분류체계 대분류
    lclsSystm2: str = None # 분류체계 중분류
    lclsSystm3: str = None # 분류체계 소분류


class TourAPIService:
    """
    해당 클래스는 tour_api_http_client로 받은  raw 데이터 정보를 가공하여 데이터를 제공하는 역할을 합니다.
    """
    def __init__(self, service_key):
        self.service_key = service_key
        self.tour_api_http_client = TourAPIHTTPClient(service_key)

    def get_area_based_list(self,
                            arrange: Arrange = None,
                            contentTypeId: ContentType = None,
                            area_info: Area = None,
                            category: Category = None,
                            modifiedtime: str = None,
                            ldong: lDong = None,
                            lclsSystem: lclsSystem = None
                            ) -> list[Place]:
        """
        해당 함수는 장소 정보를 리스트 형식으로 받아옵니다.
        각 장소 정보가 담긴 Place 객체 리스트로 받아옵니다.
        """
        raw_data = self.tour_api_http_client.get_area_based_list(
            arrange=arrange,
            contentTypeId=contentTypeId,
            area_info=area_info,
            category=category,
            modifiedtime=modifiedtime,
            ldong=ldong,
            lclsSystem=lclsSystem,
        )
        items = []
        try:
            items = raw_data['response']['body']['items']['item']
        except KeyError:
            raise HttpRequestException('tour api server exception')
        # 올바르게 데이터가 넘어왔다고 가정.

        places = []
        for each in items:
            # 각 each는 특정 장소 정보가 담긴 dictionary 형식입니다.
            place = Place()
            for key, value in each.items():
                if hasattr(place, key):
                    setattr(place, key, value) # 속성 저장
            places.append(place)
        return places

    def get_sigungu_code_as_name(self, area_code: str, target_sigungu_name: str):
        """
        해당 함수는 전국 17개 시/도 안에 포함된 특정 지역 시군구 코드를 이름을 통해서 얻고자 할 때 사용합니다.
        ex) 강남 -> 1, 아산 -> 12 (예시일 뿐이며 실제 데이터 값과 다를 수 있습니다.)
        """
        raw_data = self.tour_api_http_client.get_area_code(area_code=area_code)
        items = raw_data['response']['body']['items']['item']
        for item in items:
            if target_sigungu_name in item['name']:
                return item['code']
        return None

    def get_sigungu_name_by_code(self, area_code:str, target_sigungu_code):
        raw_data = self.tour_api_http_client.get_area_code(area_code=area_code)
        items = raw_data['response']['body']['items']['item']
        for item in items:
            if target_sigungu_code == item['code']:
                return item['name']
        return None

    def get_location_based_list(self, mapX:str, mapY:str, radius:str):
        """
            해당 함수는 위도, 경도 좌표가 주어졌을 떄 관광지 정보를 조회할 때 사용합니다.
            데이터가 없으면 빈 리스트를 반환하고, 그렇지 않다면 dictionary가 원소인 리스트가 결과 값이 반환됩니다.
        """
        raw_data = self.tour_api_http_client.get_location_based_list(
            mapX=mapX,
            mapY=mapY,
            radius=radius,
            arrange=Arrange.DISTANCE # 거리 순 조회
        )
        cnt = raw_data['response']['body']['totalCount']
        if cnt == 0:
            return []
        return raw_data['response']['body']['items']['item']




if __name__ == '__main__':
    tour_api_service = TourAPIService(PUBLIC_DATA_PORTAL_API_KEY)
    print(tour_api_service.get_sigungu_code_as_name('1', '강남'))
