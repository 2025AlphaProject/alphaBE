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
from usr.models import User
from .models import Travel, Place, Event, SnapshotImages, UserTourImage, TravelDaysAndPlaces, RelationPlace
from .serializers import EventSerializer, UserTourImageSerializer, PoseRecommendSerializer, \
    MiniRelationPlaceSerializer
from .serializers import TravelSerializer, PlaceSerializer, TravelDaysAndPlacesSerializer, \
    TravelListSerializer, TourSnapshotsSerializer
from .services import PlaceService, TravelCreationService, TravelUpdateService, TodayTravelService
from services.utils import haversine
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import Cast
from django.db.models import FloatField
from tour.poses import POSE_MAP
from tour.poses_url import POSE_URL_MAP
from tour.sido import SIDO_LIST
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination
from tour.sigungu import SIGUNGU_DATA

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
        if not area_code:
            return Response(
                {"error": "area_code 파라미터가 틀렸습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            area_code = int(area_code)
        except ValueError:
            return Response(
                {"error": "area_code는 숫자여야 합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )

        response_data = SIGUNGU_DATA.get(area_code, None)
        if not response_data:
            return Response(
                {"error": "해당 area_code 데이터가 존재하지 않습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(response_data, status=status.HTTP_200_OK)

class Sido_list(viewsets.ViewSet):

    def retrieve(self, request):
        return Response(SIDO_LIST, status=status.HTTP_200_OK)

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        place_service = PlaceService(KAKAO_REST_API_KEY)
        self.travel_creation_service = TravelCreationService(place_service)
        self.travel_update_service = TravelUpdateService(self.travel_creation_service)

    def get_queryset(self):
        return self.queryset.filter(user__sub=self.request.user.sub)

    def create(self, request, *args, **kwargs):
        """여행 상세등록 API - 최적화된 버전"""
        logger.debug("/tour/ create 메소드 실행")

        # 파라미터 유효성 검사
        places_data = request.data.get('places')
        if not places_data:
            raise NoRequiredParameterException("No Object", "places 정보가 없습니다.")

        # 여행 데이터 준비
        travel_data = request.data.copy()
        travel_data.pop('places')

        # 서비스를 통한 여행 생성
        travel = self.travel_creation_service.create_travel_with_places(
            travel_data=travel_data,
            places_data=places_data,
            user_sub=request.user.sub
        )

        # 응답 반환
        serializer = TravelSerializer(travel)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """여행 정보 수정 - 최적화된 버전"""
        travel_id = int(kwargs.get('pk'))

        # 장소 정보가 없는 경우 기본 업데이트
        places_data = request.data.get('places')
        if not places_data:
            return super().partial_update(request, *args, **kwargs)

        # 여행 데이터 준비
        travel_data = request.data.copy()
        travel_data.pop('places')

        # 서비스를 통한 업데이트
        travel = self.travel_update_service.update_travel_with_places(
            travel_id=travel_id,
            travel_data=travel_data if travel_data else None,
            places_data=places_data
        )

        serializer = TravelSerializer(travel)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        """여행 상세정보 조회 API"""
        travel_id = int(kwargs.get('pk'))
        try:
            travel = Travel.objects.get(id=travel_id)
            serializer = TravelSerializer(travel)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Travel.DoesNotExist:
            raise NoObjectException(
                error_message='해당 여행 id에 해당하는 여행이 존재하지 않습니다.'
            )

    def list(self, request, *args, **kwargs):
        self.serializer_class = TravelListSerializer
        return super().list(request, *args, **kwargs)


class BaseImageSaveView(viewsets.ModelViewSet):
    """
        해당 클래스는 여행 이미지, 인생네컷 등 사진 데이터를 저장하는 뷰로 활용됩니다.
    """

    permission_classes = [IsAuthenticated] # 로그인 사용자를 디폴트로

    def get_queryset(self):
        return self.queryset.filter(tour__user__sub=self.request.user.sub)

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


class PoseRecommendView(viewsets.ViewSet) :
    def retrieve(self, request, *args, **kwargs):
        place_id = request.GET.get('place_id', None)
        if place_id is None: raise NoRequiredParameterException()
        try:
            place = Place.objects.get(id=int(place_id))
        except Place.DoesNotExist:
            raise NoObjectException(error_message='place_id에 해당하는 장소를 찾을 수 없습니다.')

        poses = POSE_MAP.get(str(place.cat2)) # list 형태, 카테고리가 없는 경우, "None"이 키 값으로 들어갑니다.
        logger.debug(f'poses: {poses}')
        images = POSE_URL_MAP.get(str(place.cat2))
        data = {
            'place_id': place_id,
            'poses': poses,
            'images': images
        }

        serializer = PoseRecommendSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class TodayTravelViewSet(viewsets.ModelViewSet):
    """
        당일 여행에 대한 정보를 주는 API 뷰셋입니다.
        구현 메소드: GET
        들어가야 할 정보: 지역, 여행 인원수, 여행날짜, 사진 업로드 정보, 여행 장소 갯수, 관광타입정보, 여행 이름
    """
    # 유저를 가져오기 위한 로그인 여부 판단
    permission_classes = [IsAuthenticated,] # 로그인이 된 사용자만 접근을 허용합니다.

    def list(self, request, *args, **kwargs):
        # 1. 당일 여행에 대한 정보를 계산한다.
        service = TodayTravelService()
        serializer = service.get_today_tour_by_user(request.user)
        # 2. 시리얼라이저 데이터를 반환한다.
        return Response(serializer.data, status=status.HTTP_200_OK)



class LargeResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 50 # 최대 50개로


class RelationPlaceView(viewsets.ModelViewSet):
    queryset = RelationPlace.objects.all()
    serializer_class = MiniRelationPlaceSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('place_name',)
    pagination_class = LargeResultsSetPagination