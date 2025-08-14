import logging

from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.settings import SEOUL_PUBLIC_DATA_SERVICE_KEY, PUBLIC_DATA_PORTAL_API_KEY, KAKAO_REST_API_KEY, APP_LOGGER
from services.exception_handler import (
    ValidationException,
    NoRequiredParameterException,
    ValueException, NoObjectException
)
from services.tour_api import TourApi, NearEventInfo
from services.tour_api_http_client import TourAPIHTTPClient
from usr.models import User
from .models import Travel, Place, PlaceImages, Event, SnapshotImages, UserTourImage, TravelDaysAndPlaces
from .serializers import EventSerializer, UserTourImageSerializer
from .serializers import TravelSerializer, PlaceSerializer, TravelDaysAndPlacesSerializer, PlaceImageSerializer, \
    TravelListSerializer, TourSnapshotsSerializer
from .services import PlaceService
from services.utils import haversine
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import Cast
from django.db.models import FloatField

logger = logging.getLogger(APP_LOGGER)

      
class NearEventView(viewsets.ModelViewSet):
    serializer_class =  EventSerializer# 이벤트 시리얼라이저 GET
    queryset = Event.objects.all() # 이벤트 모델 GET

    def list(self, request, *args, **kwargs):
        """
        해당 함수는 tour_api의 NearEventInfo 클래스를 통해 얻어온 주변 정보를 바탕으로 주변 문화 정보를 반환해줍니다.
        """
        mapX = request.GET.get('mapX', None)
        mapY = request.GET.get('mapY', None)
        radius = request.GET.get('radius', '0.5') # 반경 정보를 가져옵니다. default: 0.5km
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)

        if mapX is None or mapY is None: # 필수 파라미터 검증
            raise NoRequiredParameterException()

        if Event.objects.count() == 0: # 주변 행사 정보가 DB에 없을 경우, 코드는 200 OK로 보냅니다.
            logger.warning("Event Info is not exist in DB") # 해당 오류는 서버 오류에 가깝기 때문에 로그를 남깁니다.
            return Response({"Message": "주변 행사 정보 데이터가 서버 내에 없습니다."}, status=status.HTTP_200_OK)

        event_info = NearEventInfo(Event, SEOUL_PUBLIC_DATA_SERVICE_KEY, Event.objects.all())
        try:
            events = event_info.get_near_by_events(float(mapY), float(mapX), float(radius)) # 주변 행사 정보를 불러옵니다.
        except ValueError:
            raise ValueException('Value Error', '경도, 위도, 반경 정보 일부 혹은 모두가 데이터 형식이 실수형이 아닙니다.')

        try:
            if start_date is not None:
                events = events.filter(start_date__gte=start_date) # 시작 날짜보다 더 크거나 같은 데이터를 불러옵니다.
            if end_date is not None:
                events = events.filter(end_date__lte=end_date) # 마지막 날짜보다 더 작거나 같은 데이터를 불러옵니다.
        except ValidationError:
            raise ValidationException(error_message="날짜 값이 날짜 형식이 아닙니다. 반드시 YYYY-MM-DD 형식이어야 합니다.")

        events = events.order_by('start_date') # 날짜 순 정렬

        serializer = self.get_serializer(events, many=True) # 시리얼라이저에 정보를 넣어 시리얼라이징합니다.
        return Response(serializer.data, status=status.HTTP_200_OK)

class AddTravelerView(viewsets.ModelViewSet):
    """
    해당 클래스는 한 여행에 다른 여행자를 추가하는 API 뷰입니다.
    """
    permission_classes = [IsAuthenticated] # 로그인 한 사용자만 허용합니다.
    serializer_class = TravelSerializer

    def create(self, request, *args, **kwargs):
        user_sub = request.data.get('add_traveler_sub', None) # post body에서 add_traveler_sub를 가져옵니다.
        travel_id = request.data.get('travel_id', None) # 추가할 여행
        if user_sub is None or travel_id is None:
            raise NoRequiredParameterException()
            # return Response({"Error": "필수 파라미터가 존재하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        travel = None
        try:
            travel = Travel.objects.get(id=int(travel_id))
            add_target_user = User.objects.get(sub=int(user_sub))
        except (Travel.DoesNotExist, User.DoesNotExist):
            logger.warning(f'travel id: {travel_id} or add_traveler_sub: {user_sub} is not exist in DB.')
            return Response({"Error": "여행과 사용자 정보가 올바르지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            travel.user.get(sub=int(request.user.sub))
        except User.DoesNotExist: # 로그인한 사용자의 것이 아닌 여행일 때
            logger.warning(f'로그인한 사용자와 요청 사용자가 일치하지 않음.')
            return Response({"ERROR": "허가되지 않은 접근"}, status=status.HTTP_403_FORBIDDEN)

        travel.user.add(add_target_user)
        serializer = self.get_serializer(travel)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GetAreaList(viewsets.ViewSet):

    def list(self, request, *args, **kwargs):
        area_code = request.GET.get('area_code', None)
        response_data = {}
        tour = TourApi(service_key=PUBLIC_DATA_PORTAL_API_KEY)
        # 전국을 다 보냅니다.
        area_list = tour.get_sigungu_code_list()
        if area_code is None:
            for each in area_list:
                response_data[each['code']] = tour.get_sigungu_code_list(int(each['code']))
        else:
            code_list = []
            for each in area_list:
                code_list.append(int(each['code']))
            area_code = int(area_code)
            if area_code not in code_list:
                raise NoObjectException('No Area Code', f"There is no area code {area_code}")
            area_list = tour.get_sigungu_code_list(area_code)
            response_data[str(area_code)] = area_list
        return Response(response_data, status=status.HTTP_200_OK)

class Sido_list(viewsets.ViewSet):

    def retrieve(self, request):
        tour = TourApi(service_key=PUBLIC_DATA_PORTAL_API_KEY)
        sido_list = tour.get_sigungu_code_list()
        return Response(sido_list, status=status.HTTP_200_OK)

class NewTourAddView(viewsets.ModelViewSet):
    """
        해당 뷰는 새로운 여행을 추가하는 뷰를 담당합니다.
        구현 API:
            여행 등록
            사용자 여행 리스트 조회
            해당 여행 상세 조회
            여행 정보 수정(장소 정보 포함)
            여행 삭제
    """

    permission_classes = [IsAuthenticated]
    queryset = Travel.objects.all() # 여행 모델에 대한 정보만 가지고 옵니다.
    serializer_class = TravelSerializer
    place_service = PlaceService(KAKAO_REST_API_KEY) # 주소 저장 서비스

    def get_most_near_place(self, fixed_x, fixed_y):
        # 10m 내에 있는 건 같은 장소라 판단
        LON_DIF_PER_10M = 0.00547202  # 경도 차
        LAT_DIF_PER_10M = 0.00009  # 위도 차
        # 주위 10m 이내 장소들을 탐색합니다.
        near_places = Place.objects.annotate(
            mapX_float=Cast('mapX', FloatField()),
            mapY_float=Cast('mapY', FloatField())
        ).filter(mapX_float__gte=(fixed_x - LON_DIF_PER_10M),
                mapX_float__lte=(fixed_x + LON_DIF_PER_10M),
                mapY_float__gte=(fixed_y - LAT_DIF_PER_10M),
                mapY_float__lte=(fixed_y + LAT_DIF_PER_10M))
        dist = None
        ans_place = None
        for place in near_places:
            temp_dist = haversine(fixed_x, fixed_y, float(place.mapX), float(place.mapY))
            if dist is None or temp_dist < dist:
                ans_place = place
                dist = temp_dist
        return ans_place


    def save_tdp_place_image(self, tour_id, places_list):
        """
            해당 함수는 장소들 리스트를 부여받으면 장소, 사진, tdp를 저장해주는 함수입니다.
            "place_ids": [1, 2, 3],
            "additional_info": [
                {
                    "place_id": 1,
                    "road_address": "",
                },
                {
                    "place_id": 2,
                    "road_address": "주소",
                },
            ]
            "custom_places": [
                {
                    "name": "아산 공세리성당",
                    "mapX": "126.9134070332",
                    "mapY": "36.8833377411",
                    "road_address": "충청남도 아산시 인주면 공세리성당길 10"
                },
                {
                    "name": "아산 공세리성당2",
                    "mapX": "126.9134070332",
                    "mapY": "36.8833377411",
                    "road_address": "충청남도 아산시 인주면 공세리성당길 10"
                },
            ]
        """
        place_ids = places_list.get('place_ids', None)
        additional_info = places_list.get('additional_info', None)
        custom_places = places_list.get('custom_places', None)
        if place_ids is not None:
            # 기존 DB에 있던 장소들 저장
            for each_id in place_ids:
                data = {
                    "place": int(each_id),
                    "travel": tour_id
                }
                serializer = TravelDaysAndPlacesSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                place = Place.objects.get(pk=int(each_id))
                road_address_kakao, address_kakao = self.place_service.get_parcel_and_road_address(float(place.mapX), float(place.mapY))
                plc_serializer = PlaceSerializer(instance=place, data={
                    "address": address_kakao,
                }, partial=True)
                plc_serializer.is_valid(raise_exception=True)
                plc_serializer.save()
                logger.debug(f'place_ids_result: {serializer.data}')

        if additional_info is not None:
            # 기존 DB 장소들 정보 업데이트
            for each in additional_info:
                place_id = each.pop('place_id', None)
                if place_id is None: raise NoRequiredParameterException(error_message='place_id 누락')

                place = None
                try:
                    place = Place.objects.get(id=int(place_id))
                except Place.DoesNotExist:
                    raise NoObjectException(error_code='NotFoundInAddIn')
                serializer = PlaceSerializer(instance=place, data=each, partial=True)
                serializer.is_valid(raise_exception=True)
                place = serializer.save()

                data = {
                    "place": int(place.id),
                    "travel": tour_id
                }
                serializer = TravelDaysAndPlacesSerializer(
                    instance=TravelDaysAndPlaces.objects.get(travel_id=tour_id, place_id=place.id),
                    data=data,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                logger.debug(f'addition_result: {place.id}: {serializer.data}')

        if custom_places is not None:
            """
                {
                    "name": "아산 공세리성당",
                    "mapX": "126.9134070332",
                    "mapY": "36.8833377411",
                    "road_address": "충청남도 아산시 인주면 공세리성당길 10"
                },
            """
            # 사용자 추가 장소들 정보 업데이트
            for each in custom_places:
                mapX = each.get('mapX', None)
                mapY = each.get('mapY', None)
                if mapX is None or mapY is None: raise NoRequiredParameterException()
                most_near_place = self.get_most_near_place(
                    float(mapX),
                    float(mapY),
                )
                ans_place = None
                if most_near_place is not None:
                    # 같은 장소일 경우
                    ans_place = most_near_place
                else:
                    # 다른 장소일 경우
                    name = each.get('name', None)
                    if name is None: raise NoRequiredParameterException()


                    road_address_kakao, address_kakao = self.place_service.get_parcel_and_road_address(
                        float(mapX), float(mapY)
                    )
                    road_address = each.get('road_address', road_address_kakao)
                    address = each.get('address', address_kakao)

                    place = Place.objects.create(
                        name=each['name'],
                        mapX=mapX,
                        mapY=mapY,
                        road_address=road_address,
                        address=address_kakao,
                    )
                    ans_place = place
                try:
                    # 중복 요청 제거
                    # 이미 연결된게 있다면
                    tdp = TravelDaysAndPlaces.objects.get(travel_id=tour_id, place_id=ans_place.id)
                except TravelDaysAndPlaces.DoesNotExist:
                    # 연결된 정보가 없어 즉, 중복이 아니라면 저장
                    data = {
                        "place": int(ans_place.id),
                        "travel": tour_id
                    }
                    serializer = TravelDaysAndPlacesSerializer(data=data)
                    serializer.is_valid(raise_exception=True)
                    serializer.save()
                    logger.debug(f'custom_place_result: {serializer.data}')

        return TravelSerializer(Travel.objects.get(id=tour_id))

    def get_queryset(self):
        logger.debug("queryset 반환 메소드 실행")
        return self.queryset.filter(user__sub=self.request.user.sub)

    def retrieve(self, request, *args, **kwargs):
        """
            여행 상세정보 조회 API
        """
        tour_id = int(kwargs.get('pk'))
        travel_object = Travel.objects.get(id=tour_id)
        deserializer = TravelSerializer(travel_object)
        return Response(deserializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        tour_id = int(kwargs.get('pk'))
        if request.data.get('places', None) is None: return super().partial_update(request, *args, **kwargs)
        logger.debug('places_update')
        data = request.data.copy()
        places_info = data.pop('places')
        serializer = TravelSerializer(Travel.objects.get(id=tour_id))
        if len(data) != 0: # 장소 제외 정보가 존재한다면
            # 여행 시리얼라이저 이용해서 저장
            serializer = TravelSerializer(Travel.objects.get(id=tour_id), # 원래 object
                                         data=data, # 요청 data
                                         partial=True) # 일부 업데이트
            serializer.is_valid(raise_exception=True)
            serializer.save()

        # self.save_tdp_place_image(tour_id, places_info)
        logger.debug('partial 장소 정보 수정 시작')
        delete_places = places_info.get('delete_places', None)
        if delete_places is not None:
            for place_id in delete_places:
                try:
                    tdp = TravelDaysAndPlaces.objects.get(travel_id=tour_id, place_id=int(place_id))
                    tdp.delete()
                except TravelDaysAndPlaces.DoesNotExist:
                    raise NoObjectException(error_message='해당 여행 장소에 맞는 여행 정보를 찾을 수 없습니다.')

        return Response(serializer.data, status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        """
            여행 상세등록 API
            "tour_name": "태근이의 여행",
            "tour_date": "2025-07-07",
            "places": {
                "place_ids": [1, 2, 3],
                "additional_info": [
                    {
                        "place_id": 1,
                        "road_address": "",
                    }
                ],
                "custom_places": [
                    {
                        "name": "아산 공세리성당",
                        "mapX": "126.9134070332",
                        "mapY": "36.8833377411",
                        "road_address": "충청남도 아산시 인주면 공세리성당길 10"
                    },
                    {
                        "name": "아산 공세리성당2",
                        "mapX": "126.9134070332",
                        "mapY": "36.8833377411",
                        "road_address": "충청남도 아산시 인주면 공세리성당길 10"
                    },
                ]
            }

        """
        logger.debug("/tour/ create 메소드 실행")
        user_sub = request.user.sub
        # 파라미터 유효성 검사 - places만
        if request.data.get('places') is None:
            raise NoRequiredParameterException("No Object", "places 정보가 없습니다.")

        # 여행 생성
        cp_dic = request.data.copy()
        cp_dic.pop('places') # 장소 정보만 삭제
        serializer = TravelSerializer(data=cp_dic)
        serializer.is_valid(raise_exception=True)
        travel = serializer.save()
        travel.user.add(User.objects.get(sub=user_sub))  # 다대 다 관계시 유저 추가
        logger.debug("여행 생성")
        # 장소 생성
        tour_id = serializer.data.get('id')
        ser = self.save_tdp_place_image(tour_id, request.data.get('places'))

        return Response(ser.data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        self.serializer_class = TravelListSerializer
        return super().list(request, *args, **kwargs)


class BaseImageSaveView(viewsets.ModelViewSet):
    """
        해당 클래스는 여행 이미지, 인생네컷 등 사진 데이터를 저장하는 뷰로 활용됩니다.
    """

    permission_classes = [IsAuthenticated] # 로그인 사용자를 디폴트로

    def get_queryset(self):
        return self.queryset.filter(user__sub=self.request.user.sub)

    def create(self, request, *args, **kwargs):
        """
            사진 저장 API
        """
        image = request.FILES.get('image', None)
        if image is None:
            raise NoRequiredParameterException(error_message='사진은 필수 입니다.')

        data = request.data.copy()
        data['user'] = request.user.sub
        data['tour'] = data.pop('tour_id', None)
        logger.debug('tour: ' + str(data['tour']))
        if data['tour'] is None:
            raise NoRequiredParameterException()
        data['tour'] = int(data['tour'][0])

        logger.debug('사진 저장 시작')
        logger.debug('request: ' + str(data))

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        obj_id = kwargs.get('pk')
        # 사진 S3에서도 삭제
        try:
            queryset_object = self.get_queryset().get(id=int(obj_id))
            if queryset_object.user != request.user:
                raise PermissionDenied(detail='본인의 사진만 저장할 수 있습니다.')
            # 사진 삭제
            queryset_object.image.delete()
        except SnapshotImages.DoesNotExist:
            raise NoObjectException(error_message='해당 id에 해당하는 사진이 없습니다.')
        return super().destroy(request, *args, **kwargs)

class TourSnapshotsView(BaseImageSaveView):
    serializer_class = TourSnapshotsSerializer
    queryset = SnapshotImages.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('tour',)


class UserTourImageView(BaseImageSaveView):
    serializer_class = UserTourImageSerializer
    queryset = UserTourImage.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('tour',)


class CategoryListView(viewsets.ViewSet):
    def retrieve(self, request, *args, **kwargs):
        """
        Tour API의 contentTypeId 기반 카테고리 리스트를 반환합니다.
        """
        category_list = [
            {"contentTypeId": 12, "name": "관광지"},
            {"contentTypeId": 14, "name": "문화시설"},
            {"contentTypeId": 15, "name": "축제/공연/행사"},
            {"contentTypeId": 28, "name": "레포츠"},
            {"contentTypeId": 32, "name": "숙박"},
            {"contentTypeId": 38, "name": "쇼핑"},
            {"contentTypeId": 39, "name": "음식점"},
        ]
        return Response(category_list, status=status.HTTP_200_OK)


class LocationBasedPoseView(viewsets.ViewSet) :
    """
            해당 뷰는 TourAPI(locationBasedList2)를 TourApi 클래스를 통해 호출하여
            반경 0.5km(=500m) 내의 관광지들을 조회하고,
            각 아이템의 cat2(세부 카테고리) 코드에 따라 추천 포즈 리스트를 부여하여 반환합니다.
            - radius 고정: 0.5km (500m)
            - 필수 파라미터: mapX(경도), mapY(위도)
        """

    POSE_MAP = {
        "A0101": ["나무나 꽃을 배경으로 양팔을 활짝 벌리고 환하게 웃기",
                  "산이나 바다를 바라보며 뒤돌아보는 옆모습 포즈",
                  "바닥에 앉아 두 손으로 얼굴을 받치고 하늘 바라보기"],
        "A0102": ["랜드마크나 조형물 앞에서 엄지척 포즈",
                  "건물이나 구조물을 손바닥 위에 올린 듯한 착시 포즈",
                  "안내판이나 간판을 가리키며 미소 짓기"],
        "A0201": ["전통 건물 앞에서 두 손을 모아 공손히 서기",
                  "옛 성문이나 성벽 위에 기대어 바라보기",
                  "한 손으로 모자를 눌러쓰며 고개를 살짝 숙이기"],
        "A0202": ["선베드나 의자에 누워 선글라스 착용 후 여유롭게 손 흔들기",
                  "바닷가나 호숫가에서 두 팔을 머리 위로 올려 스트레칭",
                  "시원한 음료를 들고 한쪽 다리를 들어 기쁘게 포즈"],
        "A0203": ["체험 도구를 들고 활짝 웃기",
                  "직접 만든 작품을 들고 카메라를 바라보기",
                  "체험 중인 모습을 옆에서 찍히는 듯 자연스럽게 연출"],
        "A0204": ["공장이나 발전소 배경으로 양손 허리에 올리고 당당한 표정",
                  "헬멧 착용 후 한 손을 들어 올려 파워풀 포즈",
                  "설비나 기계 앞에서 설명하는 듯 손짓하기"],
        "A0205": ["조형물을 손바닥 위에 올린 착시 포즈",
                  "건물 기둥이나 벽에 등을 기대고 팔짱 끼기",
                  "조형물 곡선을 따라 팔이나 다리를 똑같이 모양 맞추기"],
        "A0206": ["전시물 앞에서 손으로 턱 괴고 생각하는 표정",
                  "전시장 입구에서 티켓을 들고 미소",
                  "액자나 조형물 틈 사이로 얼굴 내밀기"],
        "A0207": ["현수막이나 무대 앞에서 손하트",
                  "친구와 어깨동무하며 활짝 웃기",
                  "축제 소품(풍선·꽃 등)을 들고 점프샷"],
        "A0208": ["무대 배경으로 브이(V) 포즈",
                  "박수 치며 환하게 웃는 순간",
                  "조명 아래에서 양팔 벌려 포즈"],
        "A0301": ["운동 장비(배트·라켓·헬멧 등)를 들고 파워풀하게 팔 들어 올리기",
                  "준비운동 스트레칭 포즈",
                  "경기장이나 트랙 배경으로 엄지척"],
        "A0302": ["달리기 시작 전 출발 자세",
                  "양손에 운동 도구(공, 라켓 등)를 들고 환하게 웃기",
                  "점프하며 손을 하늘로 뻗는 동작"],
        "A0303": ["구명조끼를 입고 한 손으로 물을 가리키며 미소",
                  "물 위에서 두 손을 들어 파도타기 포즈",
                  "오리발이나 패들 들고 활짝 웃기"],
        "A0304": ["팔을 양쪽으로 벌려 비행기 날개처럼 흉내 내기",
                  "헬멧이나 고글을 착용하고 하늘 가리키기",
                  "이륙 준비 자세로 무릎 굽혀 앉기"],
        "A0305": ["다양한 장비를 양손에 들고 브이(V) 포즈",
                  "여러 경기장 배경에서 점프샷",
                  "팀원과 함께 포옹하거나 하이파이브"],
        "A0401": ["쇼핑백을 한 손에 들고 브이(V) 포즈",
                  "쇼윈도 앞에서 한 손을 턱에 대고 고민하는 표정",
                  "양손 가득 쇼핑백을 들고 활짝 웃기"],
        "A0502": ["맛있는 음식을 한 손에 들고 엄지척",
                  "포크나 젓가락을 들고 카메라를 향해 환하게 웃기",
                  "음식 앞에서 두 손을 모아 기도하듯 “잘 먹겠습니다” 포즈"],
        "B0201": ["호텔·펜션 입구 앞에서 캐리어를 끌며 손 흔들기",
                  "침대에 앉아 두 손으로 얼굴 받치고 웃기",
                  "창가나 발코니에서 커피잔 들고 여유로운 포즈"],
        "C0112": ["가족과 손을 맞잡고 카메라를 향해 함께 웃기",
                  "아이를 번쩍 들어 올리며 즐거운 표정",
                  "모두 함께 브이(V) 포즈로 단체샷"],
        "C0113": ["한 손으로 셀카 찍으며 미소",
                  "가방을 메고 길 위를 걸으며 뒤돌아보기",
                  "카페 창가에 앉아 커피잔 들고 여유롭게 찍기"],
        "C0114": ["잔디나 나무 그늘 아래서 눈 감고 깊게 숨쉬기",
                  "하늘을 향해 두 팔 벌려 스트레칭",
                  "의자에 기대어 책을 읽는 여유로운 포즈"],
        "C0115": ["트레킹 스틱을 들고 한 발 내딛는 동작",
                  "길가 안내 표지판을 가리키며 웃기",
                  "배낭을 메고 먼 산을 바라보는 뒷모습"],
        "C0116": ["텐트 앞에서 양손을 머리 위로 올려 브이(V)",
                  "캠프파이어 앞에서 손을 모아 불 쬐기",
                  "의자에 앉아 머그컵을 들고 웃기"],
        "C0117": ["음식 한 입 크게 베어물며 즐거운 표정",
                  "여러 가지 음식을 양손에 들고 브이(V)",
                  "식탁에 차려진 음식 앞에서 두 팔 벌리기"],
    }

    def list(self, request, *args, **kwargs):
        mapX = request.GET.get('mapX', None)
        mapY = request.GET.get('mapY', None)
        radius = request.GET.get('radius', None)

        if mapX is None or mapY is None or radius is None:
            raise NoRequiredParameterException()

        try :
            float(mapX)
            float(mapY)
            float(radius)

        except ValueError :
            raise ValueException(
                'Value Error',
                '경도, 위도는 실수형, 반경은 정수형(m) 이어야 합니다.'
            )

        tour_client = TourAPIHTTPClient(service_key=PUBLIC_DATA_PORTAL_API_KEY)

        try :
            data = tour_client.get_location_based_list(
                mapX=str(mapX),
                mapY=str(mapY),
                radius=str(radius)
            )


        except Exception as e:
            logger.warning(f"TourAPIHTTPClient 호출 실패: {e}")
            return Response({"Error": "외부 API 호출에 실패했습니다."}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if items is None:
                items = []
        except Exception:
            items = []

        result_places = []
        for it in items:
            cat2 = it.get("cat2") or it.get("cat02")
            poses = self.POSE_MAP.get(str(cat2), None)

            result_places.append({
                "contentId": it.get("contentid"),
                "title": it.get("title"),
                "address": it.get("addr1"),
                "mapX": it.get("mapx"),
                "mapY": it.get("mapy"),
                "cat2": cat2,
                "poses": poses
            })

        payload = {
            "radius": float(radius),
            "mapX": float(mapX),
            "mapY": float(mapY),
            "count": len(result_places),
            "places": result_places
        }

        return Response(payload, status=status.HTTP_200_OK)