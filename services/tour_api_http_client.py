from types import FrameType
from typing import Literal

from .public_data_portal_http_client import PublicDataPortalHttpClient
from enum import Enum
from config.settings import PUBLIC_DATA_PORTAL_API_KEY
import inspect
from dataclasses import dataclass

class Area:
    """
    지역에 관한 정보를 담고 있습니다.
    Attributes:
        areaCode: 지역코드(지역코드조회 참고)
        sigunguCode: 시군구코드(지역코드조회 참고, areaCode 필수입력)
    """
    def __init__(self,
                 areaCode: str = None,
                 sigunguCode: str = None
                 ):
        self.areaCode = areaCode
        self.sigunguCode = sigunguCode
        self.__validate_parameters()

    def __validate_parameters(self):
        if self.areaCode is None and self.sigunguCode is not None: # areaCode가 없는데 sigunguCode가 들어온 경우
            raise ValueError('지역 코드 없이 시군구 코드가 들어올 수 없습니다.')

class Category:
    """
    카테고리에 관한 정보를 담고 있습니다.
    Attributes:
        cat1 (str): 대분류(서비스분류코드조회 참고)
        cat2 (str): 중분류(서비스분류코드조회 참고, cat1 필수입력)
        cat3 (str): 소분류(서비스분류코드조회 참고, cat1/cat2필수입력)
    """

    def __init__(self,
                 cat1: str = None,
                 cat2: str = None,
                 cat3: str = None):
        self.cat1 = cat1
        self.cat2 = cat2
        self.cat3 = cat3
        self.__validate_parameters()

    def __validate_parameters(self):
        if self.cat3 is not None:
            if self.cat2 is None:
                raise ValueError('파라미터 요건 불충족. 해당 클래스의 사용법을 읽어보신 후 재사용 부탁드립니다.')
            elif self.cat1 is None:
                raise ValueError('파라미터 요건 불충족. 해당 클래스의 사용법을 읽어보신 후 재사용 부탁드립니다.')
        elif self.cat2 is not None:
            if self.cat1 is None:
                raise ValueError('파라미터 요건 불충족. 해당 클래스의 사용법을 읽어보신 후 재사용 부탁드립니다.')


class lDong:
    """
    법정동 코드에 관한 클래스입니다.
    Attributes:
        lDongRegnCd (str): 법정동 시도 코드(법정동코드조회 참고)
        lDongSigunguCd (str): 법정동 시군구 코드(법정동코드조회 참고, lDongRegnCd 필수입력)
    """
    def __init__(self,
                 lDongRegnCd: str = None,
                 lDongSigunguCd: str = None):
        self.lDongRegnCd = lDongRegnCd
        self.lDongSigunguCd = lDongSigunguCd
        self.__validate_parameters()

    def __validate_parameters(self):
        if self.lDongSigunguCd is not None and self.lDongRegnCd is None:
            raise ValueError('파라미터 요건 불충족. 해당 클래스의 사용법을 읽어보신 후 재사용 부탁드립니다.')




class lclsSystem:
    """
    분류체계에 관한 클래스 입니다. (분류체계 코드 조회 (get_lcls_system_code)참고)
    Attributes:
        lclsSystem1 (str): 분류체계 1Deth(분류체계코드조회 참고)
        lclsSystem2 (str): 분류체계 2Deth(분류체계코드조회 참고, lclsSystm1 필수입력)
        lclsSystem3 (str): 분류체계 3Deth(분류체계코드조회 참고, lclsSystm1/lclsSystm2 필수입력)
    """
    def __init__(self,
                 lclsSystem1: str = None,
                 lclsSystem2: str = None,
                 lclsSystem3: str = None):
        self.lclsSystem1 = lclsSystem1
        self.lclsSystem2 = lclsSystem2
        self.lclsSystem3 = lclsSystem3
        self.__validate_parameters()

    def __validate_parameters(self):
        if self.lclsSystem3 is not None:
            if self.lclsSystem2 is None:
                raise ValueError('파라미터 요건 불충족. 해당 클래스의 사용법을 읽어보신 후 재사용 부탁드립니다.')
            elif self.lclsSystem1 is None:
                raise ValueError('파라미터 요건 불충족. 해당 클래스의 사용법을 읽어보신 후 재사용 부탁드립니다.')
        elif self.lclsSystem2 is not None:
            if self.lclsSystem1 is None:
                raise ValueError('파라미터 요건 불충족. 해당 클래스의 사용법을 읽어보신 후 재사용 부탁드립니다.')

class ContentType(Enum):
    """
    ContentType을 의미하는 이넘 클래스이며 해당 클래스가 가지고 있는 속석은 다음과 같습니다.
    관광지: GwanGwangJi
    문화사실: CultureInfra
    축제공연행사: FestivalAndConcert
    여행코스: TourCourse
    레포츠: LeisureSports
    숙박시설: Sukbak
    쇼핑: Shopping
    음식점: Restaurant
    """
    GwanGwangJi = '12'
    CultureInfra = '14'
    FestivalAndConcert = '15'
    TourCourse = '25'
    LeisureSports = '28'
    Sukbak = '32'
    Shopping = '38'
    Restaurant = '39'

class Arrange(Enum):
    """
    절렬을 의미하는 이넘이며, 해당 클래스가 가지고 있는 속성은 아래와 같습니다.
    Attribute:
        Title: 제목순
        Modify: 수정일순
        Create: 생성일순
        ImageTitle: 이미지 있는 제목순
        ImageModify: 이미지 있는 수정일순
        ImageCreate: 이미지 있는 생성일순
    """
    Title = 'A'
    Modify = 'C' # 수정일 순
    Create = 'D' # 생성일 순
    ImageTitle = 'O' # 이미지 반드시 있는 제목 순
    ImageModify = 'Q' # 이미지 반드시 있는 수정일 순
    ImageCreate = 'R' # 아마자 반드시 있는 생성일 순

class TourAPIHTTPClient:
    """
    해당 서비스는 한국관광공사_국문 관광정보 서비스_GW에서 제공하는 관광정보를 얻기 위한 클래스로 한국관광 공사와 직접 소통하는 역할을 하는 클래스입니다.
    """
    def __init__(self, service_key: str,
                 mobile_os: Literal['AND', 'IOS', 'WEB', 'ETC'] ='AND',
                 mobile_app: str = 'conever_tour_api_service',
                 response_type: Literal['json', 'xml'] = 'json',
                 num_of_rows: int = 100,):
        self.serviceKey = service_key # 서비스 키를 받습니다.
        self.MobileOS = mobile_os # mobile os 값을 받습니다.
        self.MobileApp = mobile_app # 앱 이름을 파라미터로 받습니다.
        self._type = response_type # 기본 응답 데이터를 json 형태로 고정하여 받습니다.
        self.numOfRows = num_of_rows # 한 페이지 결과 수를 의미하며 기본으로 한 번에 100개의 데이터를 받습니다.
        self.required_params = self.__upload_required_params() # 필수 파라미터를 받은 직후 코드 배치
        self.http_client = PublicDataPortalHttpClient(service_key) # 하나의 통신 클라이언트 객체를 생성합니다.

    def __upload_required_params(self):
        return self.__dict__.copy()


    def get_area_code(self, area_code: str = None):
        """
        지역코드목록을 지역,시군구 코드목록을 조회하는 기능입니다.
        :param area_code: 지역 코드를 의미하며, 해당 시/도 내의 시군구 코드 목록을 조회하기 위해서는 해당 시/도에 해당하는 지역 코드를 입력해주셔야 합니다.
        """
        path = '/areaCode2'
        params = self.required_params.copy()
        if area_code is None:
            return self.http_client.get_tour_api_response(path, **params)
        params['areaCode'] = area_code
        return self.http_client.get_tour_api_response(path, **params)



    def get_detail_pet_tour(self, content_id: str = None):
        """
        타입별 반려동물 동반 여행 정보를 조회하는 기능입니다.
        :param content_id: 해당 장소(컨텐츠)별 고유 아이디를 말하며, 미 기입시 전체 목록을 조회합니다.
        """
        path = '/detailPetTour2'
        params = self.required_params.copy()
        if content_id is None:
            return self.http_client.get_tour_api_response(path, **params)
        params['contentId'] = content_id
        return self.http_client.get_tour_api_response(path, **params)

    def get_category_code(self,
                          contentTypeId: ContentType = None,
                          category: Category = None,
                          ):
        """
        서비스분류코드목록을 대,중,소분류로 조회하는 기능
        :param contentTypeId: ContentType Enum 클래스를 사용하며, 자세한 필드 속성은 해당 클래스 주석을 참고 바랍니다.
        :param category: 카테고리를 의미하며, 자세한 필드 속성은 해당 클래스 주석을 참고 바랍니다.
        """
        path = '/categoryCode2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    def get_area_based_list(self,
                            arrange: Arrange = None,
                            contentTypeId: ContentType = None,
                            area_info: Area = None,
                            category: Category = None,
                            modifiedtime: str = None,
                            ldong: lDong = None,
                            lclsSystem: lclsSystem = None,
                            ):
        """
        지역기반 관광정보파라미터 타입에 따라서 제목순,수정일순,등록일순 정렬검색목록을 조회하는 기능

        Args:
            arrange (Arrange): 정렬 구분, 자세한 정렬 기준은 Arrange 이넘 클래스 참고
            contentTypeId (ContentType): 관광타입, 자세한 관광타입은 ContentType 이넘 클래스 참고
            area_info (Area): 지역 정보 (Area 클래스 주석 참고)
            category (Category): 카테고리 정보 (카테고리 주석 참고)
            modifiedtime (str): 수정일(형식 :YYYYMMDD)
            ldong (lDong): 법정동 정보(lDong 클래스 주석 참고)
            lclsSystem (lclsSystem): 법정 분류체계 (lclsySystem 주석 참고)

        Returns:
            The API response containing the filtered list of resources retrieved from the
            Tour API.

        Raises:
            Any error that might occur during the API request process.
        """
        path = '/areaBasedList2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    def get_location_based_list(self,
                                mapX: str,
                                mapY: str,
                                radius: str,
                                arrange: Arrange = None,
                                contentTypeId: ContentType = None,
                                modifiedtime: str = None,
                                ldong: lDong = None,
                                lclsSystem: lclsSystem = None,
                                area_info: Area = None,
                                category: Category = None,
                                ):
        """
        위치기반 관광정보파라미터 타입에 따라서 제목순,수정일순,등록일순,거리순 정렬검색목록을 조회하는 기능
        Args:
            mapX (str): GPS X좌표(WGS84 경도좌표), required
            mapY (str): GPS Y좌표(WGS84 경도좌표), required
            radius (str): 거리반경(단위:m) , Max값 20000m=20Km, required
            arrange (Arrange): 정렬 구분, 자세한 정렬 기준은 Arrange 이넘 클래스 참고
            contentTypeId (ContentType): 관광타입, 자세한 관광타입은 ContentType 이넘 클래스 참고
            area_info (Area): 지역 정보 (Area 클래스 주석 참고)
            category (Category): 카테고리 정보 (카테고리 주석 참고)
            modifiedtime (str): 수정일(형식 :YYYYMMDD)
            ldong (lDong): 법정동 정보(lDong 클래스 주석 참고)
            lclsSystem (lclsSystem): 법정 분류체계 (lclsySystem 주석 참고)
        """
        path = '/locationBasedList2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    def get_search_keyword(self,
                           keyword: str,
                           area_info: Area = None,
                           category: Category = None,
                           ldong: lDong = None,
                           lclsSystem: lclsSystem = None
                           ):
        """
        키워드로 검색을하며 전체별 타입정보별 목록을 조회한다
        """
        path = '/searchKeyword2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    def get_search_festival(self,
                            eventStartDate: str,
                            eventEndDate: str = None,
                            arrange: Arrange = None,
                            area_info: Area = None,
                            category: Category = None,
                            ldong: lDong = None,
                            lclsSystem: lclsSystem = None,
                            modifiedtime: str = None,
                            ):
        path = '/searchFestival2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    def get_search_sukbak(self,
                          lDongRegnCd: str,
                          lDongSigunguCd: str = None,
                          arrange: Arrange = None,
                          area_info: Area = None,
                          category: Category = None,
                          lclsSystem: lclsSystem = None,
                          modifiedtime: str = None):
        """
        숙박정보 검색목록을 조회한다. 컨텐츠 타입이 ‘숙박’일 경우에만 유효하다.
        """
        path = '/searchStay2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    # def get_detail_common(self):
    #     """
    #     타입별공통 정보기본정보,약도이미지,대표이미지,분류정보,지역정보,주소정보,좌표정보,개요정보,길안내정보,이미지정보,연계관광정보목록을 조회하는 기능
    #     """
    #     path = '/detailCommon2'
    #     params = self.__upload_all_parameters(inspect.currentframe())
    #     return self.http_client.get_tour_api_response(path, **params)

    # def get_detail_intro(self):
    #     """
    #     상세소개 쉬는날, 개장기간 등 내역을 조회하는 기능
    #     """
    #     path = '/detailIntro2'
    #     params = self.__upload_all_parameters(inspect.currentframe())
    #     return self.http_client.get_tour_api_response(path, **params)

    # def get_detail_info(self):
    #     """
    #     추가 관광정보 상세내역을 조회한다. 상세반복정보를 안내URL의 국문관광정보 상세 매뉴얼 문서를 참고하시기 바랍니다.
    #     """
    #     path = '/detailInfo2'
    #     params = self.__upload_all_parameters(inspect.currentframe())
    #     return self.http_client.get_tour_api_response(path, **params)

    # def get_detail_image(self):
    #     """
    #     관광정보에 매핑되는 서브이미지목록 및 이미지 자작권 공공누리유형을 조회하는 기능
    #     """
    #     path = '/detailImage2'
    #     params = self.__upload_all_parameters(inspect.currentframe())
    #     return self.http_client.get_tour_api_response(path, **params)

    def get_lcls_system_code(self, lclsSystem: lclsSystem = None, lclsSystemListYn: Literal['Y', 'N'] = 'Y'):
        """
        분류체계코드목록을 1Deth, 2Deth, 3Deth 코드별 조회하는 기능
        """
        path = '/lclsSystemCode2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    def get_area_based_sync_list(self,
                                 showflag: str = None,
                                 arrange: Arrange = None,
                                 contentTypeId: ContentType = None,
                                 area_info: Area = None,
                                 category: Category = None,
                                 ldong: lDong = None,
                                 lclsSystem: lclsSystem = None,
                                 modifiedtime: str = None,
                                 oldContentId: str = None,):
        """
        지역기반 관광정보파라미터 타입에 따라서 제목순,수정일순,등록일순 정렬검색목록을 조회하는 기능
        """
        path = '/areaBasedSyncList2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    def get_ldong_code(self,
                       lDongRegnCd: str = None,
                       lDongListYn: Literal['Y', 'N'] = 'Y',
                       ):
        """
        법정동코드 목록을 시도,시군구 코드별 조회하는 기능
        Args:
            lDongRegnCd (str): 법정동 시도코드 ( lDongRegnCd 해당되는 법정동 시군구코드 조회 , 입력이 없을시 전체 시도목록 호출 )
            lDongListYn (str): 법정동 목록조회 여부(N:코드조회 , Y:전체목록조회)
        """
        path = 'ldongCode2'
        params = self.__upload_all_parameters(inspect.currentframe())
        return self.http_client.get_tour_api_response(path, **params)

    def __upload_all_parameters(self, frame: FrameType):
        """
        모든 파라미터 업로드 진행 후 요청 보낼 최종 파라미터를 뽑아냅니다.
        """
        arg_info = inspect.getargvalues(frame)
        params = self.required_params.copy()
        for arg in arg_info.args[1:]: # 1번 부터 시작 (self 제거)
            if arg_info.locals[arg] is not None:
                if type(arg_info.locals[arg]).__module__ != 'builtins' and not isinstance(arg_info.locals[arg], Enum): # 클래스 인스턴스라면
                    for each in arg_info.locals[arg].__dict__:
                        if arg_info.locals[arg].__dict__[each] is not None:
                            params[each] = arg_info.locals[arg].__dict__[each]
                else:
                    params[arg] = arg_info.locals[arg] if not isinstance(arg_info.locals[arg], Enum) else arg_info.locals[arg].value
        return params



if __name__ == '__main__':
    tour_api_service = TourAPIHTTPClient(PUBLIC_DATA_PORTAL_API_KEY)
    print(tour_api_service.get_area_based_list(contentTypeId=ContentType.Sukbak, arrange=Arrange.ImageTitle))
    # area = Area()
    # area.areaCode = 'sdf'
    # print(area.__dict__)
    # print(area.areaCode)