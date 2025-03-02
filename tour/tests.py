from django.test import TestCase
from config.settings import PUBLIC_DATA_PORTAL_API_KEY # 공공 데이터 포탈 앱 키
from .modules.tour_api import (
    TourApi,
    MobileOS,
    AreaCode,
    Area,
    Arrange,
    Category1Code,
    ContentTypeId,
)

# Create your tests here.

class TestTour(TestCase):
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
        for each in response:
            print(each.get_eventStartDate(), each.get_eventEndDate())
