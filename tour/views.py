from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from usr.models import User
from .serializers import TravelSerializer, PlaceSerializer, TravelDaysAndPlacesSerializer, PlaceImageSerializer, \
    TravelListSerializer, TourSnapshotsSerializer
from config.settings import SEOUL_PUBLIC_DATA_SERVICE_KEY, PUBLIC_DATA_PORTAL_API_KEY, KAKAO_REST_API_KEY, APP_LOGGER
from .serializers import EventSerializer
from services.tour_api import TourApi, NearEventInfo
from .services import PlaceService
from .models import Travel, Place, PlaceImages, Event, UserTourImages
import logging
from services.exception_handler import (
    ValidationException,
    NoRequiredParameterException,
    ValueException, NoObjectException
)

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
            # return Response({"ERROR": "필수 파라미터 중 일부 혹은 전체가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

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

    def save_tdp_place_image(self, tour_id, places_list):
        """
            해당 함수는 장소들 리스트를 부여받으면 장소, 사진, tdp를 저장해주는 함수입니다.
        """
        for each in places_list:
            """
                {
                    name
                    mapX
                    mapY
                    image_url
                    road_address
                    address
                }
            """
            # 파라미터 검증
            if each.get('name', None) is None or each.get('mapX', None) is None or each.get('mapY', None) is None:
                raise NoRequiredParameterException(error_message='장소의 필수 파라미터 누락')

            plc_cp_dic = each.copy()
            img_url = plc_cp_dic.pop('image_url', None) # 사진 정보는 따로 저장
            road_address_kakao, address_kakao = self.place_service.get_parcel_and_road_address(float(each['mapX']), float(each['mapY']))
            if plc_cp_dic.get('road_address', None) is None:
                plc_cp_dic['road_address'] = road_address_kakao
            plc_cp_dic['address'] = address_kakao
            place_serializer = PlaceSerializer(data=plc_cp_dic)
            place_serializer.is_valid(raise_exception=True)
            place_serializer.save()
            logger.debug(f"장소 저장")

            # 사진 저장
            plc_id = place_serializer.data.get('id')
            place = Place.objects.get(id=int(plc_id))
            if img_url is not None and img_url != "":
                image_serializer = PlaceImageSerializer(data={
                    'place': int(plc_id),
                    'image_url': img_url
                })
                image_serializer.is_valid(raise_exception=True)
                image_serializer.save()
                logger.debug(f"사진 저장")

            tdp_serializer = TravelDaysAndPlacesSerializer(data={
                'place': int(plc_id),
                'travel': int(tour_id)
            })
            tdp_serializer.is_valid(raise_exception=True)
            tdp_serializer.save()
            logger.debug(f"tdp 저장")
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
        for each in places_info:
            info_data = each.copy()
            place_id_str = info_data.get('id', None)
            image_url = info_data.pop('image_url', None)
            if place_id_str is None: raise NoRequiredParameterException(error_message='각 장소 정보에 장소 id는 필수입니다.')

            try:
                place = Place.objects.get(id=int(place_id_str)) # 기존 장소 객체 불러오기
            except Place.DoesNotExist:
                raise NoObjectException(error_code='No place', error_message='id에 맞는 장소 정보가 없습니다.')

            mapX = info_data.get('mapX', None)
            mapY = info_data.get('mapY', None)
            logger.debug('좌표: ' + str(mapX) + ' ' + str(mapY))
            if info_data.get('mapX', None) is not None or info_data.get('mapY', None) is not None: # 좌표 변경 시
                logger.debug('좌표 변경에 따른 주소 변경 시작')
                if mapX is None: mapX = place.mapX
                if mapY is None: mapY = place.mapY

                road_addr, addr = self.place_service.get_parcel_and_road_address(float(mapX), float(mapY))
                if info_data.get('road_address') is None: info_data['road_address'] = road_addr
                info_data['address'] = addr


            place_serializer = PlaceSerializer(place, data=info_data, partial=True)
            place_serializer.is_valid(raise_exception=True)
            place_serializer.save()

            if image_url is not None:
                logger.debug('partial 사진저장 시작')
                place_image_serializer = PlaceImageSerializer(
                    PlaceImages.objects.get(place_id=int(place_id_str)),
                    data={"image_url": image_url}, partial=True
                )
                place_image_serializer.is_valid(raise_exception=True)
                place_image_serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


    def create(self, request, *args, **kwargs):
        """
            여행 상세등록 API
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

class TourSnapshotsView(viewsets.ModelViewSet):
    serializer_class = TourSnapshotsSerializer
    queryset = UserTourImages.objects.all()
    permission_classes = [IsAuthenticated] # 로그인 사용자만 허용

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
        snapshot_id = kwargs.get('pk')
        # 사진 S3에서도 삭제
        try:
            snapshot_object = UserTourImages.objects.get(id=int(snapshot_id))
            if snapshot_object.user != request.user:
                raise PermissionDenied(detail='본인의 사진만 저장할 수 있습니다.')
            # 사진 삭제
            snapshot_object.image.delete()
        except UserTourImages.DoesNotExist:
            raise NoObjectException(error_message='해당 id에 해당하는 사진이 없습니다.')
        return super().destroy(request, *args, **kwargs)

