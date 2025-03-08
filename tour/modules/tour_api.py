import requests
from enum import Enum

class Area:
    def __init__(self, raw_dict):
        self.__address = raw_dict['addr1']
        self.__area_code = raw_dict['areacode']
        self.__category1 = raw_dict['cat1']
        self.__category2 = raw_dict['cat2']
        self.__category3 = raw_dict['cat3']
        self.__contentId = raw_dict['contentid']
        self.__contentTypeId = raw_dict['contenttypeid']
        self.__image1_url = raw_dict['firstimage']
        self.__image2_url = raw_dict['firstimage2']
        self.__mapX = raw_dict['mapx']
        self.__mapY = raw_dict['mapy']
        self.__title = raw_dict['title']
        self.__eventStartDate = raw_dict.get('eventstartdate', None)
        self.__eventEndDate = raw_dict.get('eventenddate', None)

    @staticmethod
    def from_raw_list_to_area_list(raw_list):
        list = []
        for item in raw_list:
            list.append(Area(item))
        return list

    def get_address(self):
        return self.__address

    def get_area_code(self):
        return self.__area_code

    def get_category1(self):
        return self.__category1

    def get_category2(self):
        return self.__category2

    def get_category3(self):
        return self.__category3

    def get_contentId(self):
        return self.__contentId

    def get_contentTypeId(self):
        return self.__contentTypeId

    def get_image1_url(self):
        return self.__image1_url

    def get_image2_url(self):
        return self.__image2_url

    def get_mapX(self):
        return self.__mapX

    def get_mapY(self):
        return self.__mapY

    def get_title(self):
        return self.__title

    def get_eventStartDate(self):
        return self.__eventStartDate

    def get_eventEndDate(self):
        return self.__eventEndDate

    def __str__(self):
        return self.get_title()

    def __repr__(self):
        return self.__str__()



class AreaCode(Enum):
    """
    전국 17개 시/도 지역 코드입니다.
    """
    SEOUL = 1
    INCHEON = 2
    DAEJEON = 3
    DAEGU = 4
    GWANGJU = 5
    BUSAN = 6
    ULSAN = 7
    SEJONG = 8
    GYEONGGI = 31
    KANGWON = 32
    CHUNGBUK = 33
    CHUNGNAM = 34
    GYUNGBUK = 35
    GYUNGNAM = 36
    JEONBUK = 37
    JEONNAM = 38
    JEJU = 39

class Category1Code(Enum):
    """
    대분류 코드 Enum입니다.
      - 자연: NATURE
      - 인문: HUMANITIES
      - 레포츠: LEIPORTS
      - 쇼핑: SHOPPING
      - 음식: FOOD
      - 숙박: SLEEPING_FACILITY
      - 추천코스: RECOMMENDED_COURSE
    """
    NATURE = 'A01'
    HUMANITIES = 'A02'
    LEIPORTS = 'A03'
    SHOPPING = 'A04'
    FOOD = 'A05'
    SLEEPING_FACILITY = 'B02'
    RECOMMENDED_COURSE = 'C01'



class ContentTypeId(Enum):
    """
    관광지: GWANGWANGJI
    문화시설: MUNHWASISUL
    축제공연행사: CHUKJAEGONGYEONHAENGSA
    여행코스: YEOHAENGCOURSE
    레포츠: LEIPORTS
    숙박: SUKBAK
    쇼핑: SHOPPING
    음식점: EUMSIKJUM
    """
    GWANGWANGJI = 12
    MUNHWASISUL = 14
    CHUKJAEGONGYEONHAENGSA = 15
    YEOHAENGCOURSE = 25
    LEIPORTS = 28
    SUKBAK = 32
    SHOPPING = 38
    EUMSIKJUM = 39

class MobileOS(Enum):
    """
    모바일 운영체제\n
    안드로이드: ANDROID\n
    IOS: IOS\n
    윈도우 폰: WINDOW_PHONE\n
    그 외: ETC
    """
    ANDROID = 'AND'
    IOS = 'IOS'
    WINDOW_PHONE = 'WIN'
    ETC = 'ETC'

class Arrange(Enum):
    """
    이미지 구분 X 정렬 \n
    - 제목순: TITLE
    - 수정일순: MODIFY
    - 생성일순: CREATION
    대표이미지가 있는 정렬 \n
    - 제목순: TITLE_IMAGE
    - 수정일순: MODIFY_IMAGE
    - 생성일순: CREATION_IMAGE
    """
    TITLE = 'A'
    MODIFY = 'C'
    CREATION = 'D'
    TITLE_IMAGE = 'O'
    MODIFY_IMAGE = 'Q'
    CREATION_IMAGE = 'R'


# 한국 관광정보 api를 위한 베이스 URL
BASE_URL = 'http://apis.data.go.kr/B551011/KorService1'

class TourApi:
    """
    해당 클래스는 한국관광공사_국문 관광정보 서비스_GW API를 조금 더 쉽게 사용하기 위해 만들어진 클래스 입니다.
    """

    def __init__(self, MobileOS, MobileApp, service_key=None):
        """
        모바일 운영체제, 모바일 앱 이름을 파라미터로 받습니다.
        :param MobileOS:
        :param MobileApp:
        """
        self.set_MobileOS(MobileOS)
        self.set_MobileApp(MobileApp)
        self.set_serviceKey(service_key)


    def set_serviceKey(self, serviceKey):
        self.__serviceKey = serviceKey # API 키를 추가합니다.


    def set_MobileOS(self, MobileOS):
        """
        :param MobileOS: OS 구분 : IOS (아이폰), AND (안드로이드), WIN (윈도우폰), ETC(기타) => MobileOS Enum 활용해도 됨
        """
        self.MobileOS = MobileOS.value if isinstance(MobileOS, Enum) else MobileOS

    def set_MobileApp(self, MobileApp):
        """
        :param MobileApp: 서비스명(어플명)
        :return:
        """
        self.MobileApp = MobileApp

    def __upload_required_params(self):
        parameters = dict()
        parameters['serviceKey'] = self.__serviceKey
        parameters['mobileOS'] = self.MobileOS
        parameters['mobileApp'] = self.MobileApp
        parameters['_type'] = 'json'
        parameters['numOfRows'] = 30 # 디폴트로 30개로 제한
        return parameters

    def get_sigungu_code_list(self, areaCode):
        """
        각 시/도 내의 세부 지역 코드를 가져옵니다.
        :param areaCode: 지역 번호를 의미합니다. AreaCode enum 사용가능
        :return: 지역 코드 리스트를 반환합니다.
        """
        uri = '/areaCode1'
        parameters = self.__upload_required_params()
        parameters['numOfRows'] = 100 # 한번에 100개의 정보를 보여줍니다.
        parameters['areaCode'] = areaCode.value if isinstance(areaCode, Enum) else areaCode
        response = requests.get(BASE_URL + uri, params=parameters)
        if response.status_code == 200:
            if response.json()['response']['body']['totalCount'] == 0: # 컨텐츠가 없으면 빈 리스트 반환
                return []
            return response.json()['response']['body']['items']['item']
        return None

    def get_sigungu_code(self, areaCode, targetName):
        """
        해당 함수는 targetName에 대응되는 정확한 지역 코드를 받기 위한 함수입니다.
        :param areaCode: 시/도에 해당하는 지역 번호를 의미합니다. AreaCode enum 사용가능
        :param targetName: 시/도 안에서 찾고 싶은 지역 이름을 의미합니다. ex) 아산시
        :return: 지역 코드를 반환합니다. 없으면 None
        """
        list = self.get_sigungu_code_list(areaCode)
        for item in list:
            if item['name'] == targetName or (targetName in item['name']):
                return int(item['code'])
        return None

    def get_location_based_list(self, mapX, mapY, radius):
        """
    한국 관광정보 API의 locationBasedList1 엔드포인트를 호출하여, 위치 기반 관광정보 목록을 반환합니다.

    이 함수는 필수 파라미터 외에 kwargs를 통해 다양한 옵션 파라미터를 받을 수 있으며, 전달된 값들은 API 호출 시 사용됩니다.
    **필수 파라미터**
      - mapX: GPS X좌표(WGS84 경도좌표)
      - mapY: GPS Y좌표(WGS84 위도좌표)
      - radius: 거리반경(단위:m) , Max값 20000m=20Km

    이 외에 kwargs에 포함될 수 있는 파라미터는 다음과 같습니다:

    **선택 파라미터:**
      - numOfRows: 한 페이지에 표시할 결과 수
      - pageNo: 요청할 페이지 번호
      - listYN: 목록 구분 (Y=목록, N=개수)
      - arrange: 정렬 기준 (아래 값 혹은 Arrange Enum 클래스 이용)
            * A: 제목순
            * C: 수정일순
            * D: 생성일순
            * O: 제목순 (대표이미지 필수)
            * Q: 수정일순 (대표이미지 필수)
            * R: 생성일순 (대표이미지 필수)
      - contentTypeId: 관광타입 ID (or ContentTypeId Enum 이용)
            * 예: 12 (관광지), 14 (문화시설), 15 (축제공연행사), 25 (여행코스), 28 (레포츠), 32 (숙박), 38 (쇼핑), 39 (음식점)
      - areaCode: 지역 코드 (지역코드 조회 참고)
      - sigunguCode: 시군구 코드 (지역코드 조회 참고)
      - cat1: 대분류 코드 (서비스 분류 코드 조회 참고)
      - cat2: 중분류 코드 (서비스 분류 코드 조회 참고)
      - cat3: 소분류 코드 (서비스 분류 코드 조회 참고)
      - modifiedtime: 수정일 (형식: YYYYMMDD)

    :return: API 호출이 성공하면 Area 객체 형식의 결과를 반환하며, 실패 시 None을 반환합니다.
    """
        uri = '/locationBasedList1'
        parameters = self.__upload_required_params()
        parameters['mapX'] = mapX
        parameters['mapY'] = mapY
        parameters['radius'] = radius
        response = requests.get(BASE_URL + uri, params=parameters)
        if response.status_code == 200:
            if response.json()['response']['body']['totalCount'] == 0: # 컨텐츠가 없으면 빈 리스트 반환
                return []
            return Area.from_raw_list_to_area_list(response.json()['response']['body']['items']['item'])
        return None


    def get_area_based_list(self, **kwargs):
        """
    한국 관광정보 API의 areaBasedList1 엔드포인트를 호출하여, 지역 기반 관광정보 목록을 반환합니다.

    이 함수는 kwargs를 통해 다양한 옵션 파라미터를 받을 수 있으며, 전달된 값들은 API 호출 시 사용됩니다.
    kwargs에 포함될 수 있는 파라미터는 다음과 같습니다:

    **선택 파라미터:**
      - numOfRows: 한 페이지에 표시할 결과 수
      - pageNo: 요청할 페이지 번호
      - listYN: 목록 구분 (Y=목록, N=개수)
      - arrange: 정렬 기준 (아래 값 혹은 Arrange Enum 클래스 이용)
            * A: 제목순
            * C: 수정일순
            * D: 생성일순
            * O: 제목순 (대표이미지 필수)
            * Q: 수정일순 (대표이미지 필수)
            * R: 생성일순 (대표이미지 필수)
      - contentTypeId: 관광타입 ID (or ContentTypeId Enum 이용)
            * 예: 12 (관광지), 14 (문화시설), 15 (축제공연행사), 25 (여행코스), 28 (레포츠), 32 (숙박), 38 (쇼핑), 39 (음식점)
      - areaCode: 지역 코드 (지역코드 조회 참고)
      - sigunguCode: 시군구 코드 (지역코드 조회 참고)
      - cat1: 대분류 코드 (서비스 분류 코드 조회 참고)
      - cat2: 중분류 코드 (서비스 분류 코드 조회 참고)
      - cat3: 소분류 코드 (서비스 분류 코드 조회 참고)
      - modifiedtime: 수정일 (형식: YYYYMMDD)

    :return: API 호출이 성공하면 Area 객체 형식의 결과를 반환하며, 실패 시 None을 반환합니다.
    """
        uri = '/areaBasedList1'
        # not required parameters
        list = ['numOfRows',
                'pageNo',
                'listYN',
                'arrange',
                'contentTypeId',
                'areaCode',
                'sigunguCode',
                'cat1',
                'cat2',
                'cat3',
                'modifiedtime',
                ]
        # 보낼 정보 저장
        parameters = self.__upload_required_params()
        # None이 아닌 모든 값을 딕셔너리 형태로 저장
        for each in list:
            if each in kwargs:
                if isinstance(kwargs[each], Enum): # 들어오는 형식이 enum 형식이라면
                    parameters[each] = kwargs[each].value
                else:
                    parameters[each] = kwargs[each]
        response = requests.get(BASE_URL + uri, params=parameters)
        if response.status_code == 200:
            if response.json()['response']['body']['totalCount'] == 0: # 컨텐츠가 없으면 빈 리스트 반환
                return []
            return Area.from_raw_list_to_area_list(response.json()['response']['body']['items']['item'])
        return None

    def get_image_urls(self, contentId):
        """
        관광정보에 매핑되는 서브이미지목록 및 이미지 자작권 공공누리유형을 조회하는 기능으로, get_area_based_list 함수로 가져온 사진 정보와 다른 이미지 리스트를 가져옵니다.
        :param contentId: 컨텐츠 아이디 (각 api로 얻은 관광지(지역) 고유 컨텐츠 아이디)
        :return:
        """
        uri = '/detailImage1'
        parameters = self.__upload_required_params()
        parameters['contentId'] = contentId
        parameters['subImageYN'] = 'Y' # 원본,썸네일이미지조회,공공누리 저작권유형정보조회
        response = requests.get(BASE_URL + uri, params=parameters)
        if response.status_code == 200:
            returnList = []
            if response.json()['response']['body']['totalCount'] == 0: # 컨텐츠가 없으면 빈 리스트 반환
                return returnList
            raw = response.json()['response']['body']['items']['item']

            for item in raw:
                returnList.append(item['originimgurl'])
            return returnList
        return None

    def get_category_code_list(self, **kwargs):
        """
        한국 관광정보 API의 areaBasedList1 엔드포인트를 호출하여, 지역 기반 관광정보 목록을 반환합니다.

        이 함수는 kwargs를 통해 다양한 옵션 파라미터를 받을 수 있으며, 전달된 값들은 API 호출 시 사용됩니다.
        kwargs에 포함될 수 있는 파라미터는 다음과 같습니다:

        **선택 파라미터**
          - numOfRows: 한 페이지에 표시할 결과 수
          - pageNo: 요청할 페이지 번호
          - contentTypeId: 관광타입 ID (ContentTypeId Enum 이용)
          - cat1: 대분류 코드 (cat1 파라미터 없을 시 대분류 코드들 출력)
          - cat2: 중분류 코드 (대분류 코드 파라미터 필수, cat2 파라미터 없을 시 중분류 코드들 반환)
          - cat3: 소분류 코드 (중분류 코드 파라미터 필수, cat3 파라미터 없을 시 소분류 코드들 반환)
        :param kwargs:
        :return: JSON 형식으로, 분류코드에 해당하는 'code'와 그에 대응되는 이름 정보인 'name' 키 값이 포함
        """
        uri = '/categoryCode1'
        parameters = self.__upload_required_params()
        for each in kwargs.keys():
            parameters[each] = kwargs[each].value if isinstance(kwargs[each], Enum) else kwargs[each]
        response = requests.get(BASE_URL + uri, params=parameters)
        if response.status_code == 200:
            if response.json()['response']['body']['totalCount'] == 0: # 컨텐츠가 없으면 빈 리스트 반환
                return []
            raw = response.json()['response']['body']['items']['item']
            for each in raw:
                each.pop('rnum')
            return raw
        return None

    def get_festival_list(self, event_start_date, event_end_date, **kwargs):
        """
        해당 함수는 행사 정보를 얻는 데 초점을 둔 함수 입니다.
        :param event_start_date: 이벤트 시작 날짜 (여행 시작 날짜, YYYYMMDD 형식)
        :param event_end_date: 이벤트 마감 날짜(여행 마감 날짜, YYYYMMDD 형식)
        """
        uri = '/searchFestival1'
        parameters = self.__upload_required_params()
        parameters['eventStartDate'] = event_start_date
        parameters['eventEndDate'] = event_end_date
        for each in kwargs.keys():
            parameters[each] = kwargs[each].value if isinstance(kwargs[each], Enum) else kwargs[each]

        response = requests.get(BASE_URL + uri, params=parameters)
        if response.status_code == 200:
            if response.json()['response']['body']['totalCount'] == 0: return []
            raw = response.json()['response']['body']['items']['item']
            return Area.from_raw_list_to_area_list(raw)


import math
from tour.models import Event

# 주변 행사 정보를 가져오는 목적의 클래스를 제작합니다.
class NearEventInfo:
    def __init__(self, service_key, all_events=None):
        self.all_events = all_events
        self.service_key = service_key

    def set_service_key(self, service_key):
        """
        service키 설정
        """
        self.service_key = service_key

    @staticmethod
    def haversine(map_y1, map_x1, map_y2, map_x2):
        """
        두 지점의 위도와 경도 정보가 주어질 때 두 지점 사이의 거리를 구하는 함수입니다.
        :param map_x1: 경도 좌표 1
        :param map_y1: 위도 좌표 1
        :param map_x2: 경도 좌표 2
        :param map_y2: 위도 좌표 2
        """

        R = 6378  # 지구 반지름 (단위: km)

        # 위도 및 경도를 라디안 단위로 변환
        map_x1, map_y1, map_x2, map_y2 = map(math.radians, [map_x1, map_y1, map_x2, map_y2])

        # 위도, 경도의 차이 계산
        d_y = map_y2 - map_y1
        d_x = map_x2 - map_x1

        # haversine 공식 적용
        a = math.sin(d_y / 2) ** 2 + math.cos(map_y1) * math.cos(map_y2) * math.sin(d_x / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c  # 거리 계산
        return distance

    def get_near_by_events(self, my_y, my_x, all_events=None):
        """
        db에서 위도 경도 좌표차를 이용해서 대략적으로 근처에 있는 행사 정보들만 추출합니다.
        :param all_events: places.objects.all()과 같은 장소 정보 전체 데이터를 말합니다.
        :param my_y: 타겟 장소 경도 좌표입니다.
        :param my_x: 타겟 장소 위도 좌표입니다.
        :return: 필터된 장소들을 반환합니다.
        """
        self.all_events = all_events
        if self.all_events is None: # 만약 모든 events 객체가 없다면
            raise Exception("There are not all_events objects")

        # 만약 all_events 객체가 Event 인스턴스가 아니라면 오류를 발생시킵니다.
        if not isinstance(all_events, Event):
            raise Exception("all_events are not a Event objects")

        # 경도 차가 0.273601, 위도 차가 0.0045일 때 500m 차이가 납니다. -> 경도 차 0.0547202: 0.1km 위도 차 0.0009: 0.1km
        filtered_events = self.__get_events_in_shadow_box(my_y, my_x, 0.5) # 0.5km 사각형 내에 있는 장소정보들을 가져옵니다.
        result_events = self.__get_events_in_radius_box(filtered_events) # 0.5km 반경 내에 있는 장소정보들을 가져옵니다.
        return result_events

    def __get_events_in_shadow_box(self, target_y, target_x, distance):
        """
        상하 좌우 distance (단위: km)만큼 떨어진 곳을 한 변으로 하여 사각형을 그렸을 때, 그 사각형 안에 있는 장소들을 가져옵니다.
        :return: Event 객체들을 반환합니다.
        """
        self.distance = distance # 거리 설정
        self.target_y = target_y
        self.target_x = target_x
        # 경도 차가 0.273601, 위도 차가 0.0045일 때 500m 차이가 납니다. -> 경도 차 0.0547202: 0.1km 위도 차 0.0009: 0.1km
        LON_DIF_PER_100M = 0.0547202 # 경도 차
        LAT_DIF_PER_100M = 0.0009 # 위도 차
        mul = distance / 0.1 # 기준 단위가 0.1km로 되어 있기 때문에 곱수를 구합니다.
        lon_dif = mul * LON_DIF_PER_100M
        lat_dif = mul * LAT_DIF_PER_100M
        # Places 필드를 기준으로 작성되었습니다.
        # TODO Places 필드 변경시 변경 작성 바랍니다.
        filtered_events = self.all_events.filter(mapX__gte=(target_x - lon_dif),
                                                 mapX__lte=(target_x + lon_dif),
                                                 mapY__gte=(target_y - lat_dif),
                                                 mapY__lte=(target_y + lat_dif))
        return filtered_events


    def __get_events_in_radius_box(self, filtered_places):
        """
        타겟 장소 기준 반경 self.distance 만큼 떨어진 장소들을 가져옵니다. 반드시 get_places_in_shadow_box를 통해 선별된 장소들이어야 합니다.
        :return: Event 객체들을 반환합니다.
        """
        return_list_id = []
        for each_place in filtered_places:
            x = each_place.mapX # 경도 좌표 추출
            y = each_place.mapY # 위도 좌표 추출
            dif = self.haversine(self.target_y, self.target_x, y, x)
            if dif < self.distance: # 설정한 거리보다 작다면
                return_list_id.append(each_place.id)
        return Event.objects.filter(id__in=return_list_id)

