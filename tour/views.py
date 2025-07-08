from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

import tour
from usr.models import User
from .serializers import TravelSerializer, PlaceSerializer, TravelDaysAndPlacesSerializer, PlaceImageSerializer
from config.settings import SEOUL_PUBLIC_DATA_SERVICE_KEY, PUBLIC_DATA_PORTAL_API_KEY, KAKAO_REST_API_KEY, APP_LOGGER
from .serializers import EventSerializer
from services.tour_api import TourApi, NearEventInfo
from .services import PlaceService
from .models import Travel, Place, TravelDaysAndPlaces, PlaceImages, Event
import datetime
import logging
from services.exception_handler import (
    ValidationException,
    NoAttributeException,
    NoRequiredParameterException,
    ValueException, NoObjectException
)

logger = logging.getLogger(APP_LOGGER)


class TravelViewSet(viewsets.ModelViewSet):
    """
        해당 API는 사용자의 여행을 등록하는 api입니다.
    """
    queryset = Travel.objects.all()
    serializer_class = TravelSerializer
    permission_classes = [IsAuthenticated] # 로그인한 사용자만 api를 승인합니다.

    def create(self, request, *args, **kwargs):  # 새로운 여행 등록 API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기

        # request.data를 변경 가능한 딕셔너리로 변환 후 user 추가
        travel_data = dict(request.data).copy()
        # travel_data["user"] = user_sub # 다대일 관계시 유저 추가

        serializer = self.get_serializer(data=travel_data)  # 수정된 데이터로 serializer 초기화
        serializer.is_valid(raise_exception=True)
        travel = serializer.save()  # ORM을 이용해 저장
        travel.user.add(User.objects.get(sub=user_sub))  # 다대 다 관계시 유저 추가
        data = self.get_serializer(travel).data

        # json 응답을 반환
        return Response(data, status=status.HTTP_201_CREATED)

      
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

            place = Place.objects.get(id=int(place_id_str)) # 기존 장소 객체 불러오기

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




class CourseView(viewsets.ViewSet):

    def __validate_parameters_in_post(self, tour_id, date, places, user_sub) -> tuple[int, str]:
        """
            해당 함수는 post 요청이 들어왔을 때 정상적으로 파라미터가 왔는지 검사히기 위한 로직입니다.
            1. places가 리스트 형식인지 확인
            2. 필수 파라미터가 존재하는지 확인
            3. 파라미터 중, date 형식이 맞는지 확인
            4. 실제로 여행 id가 존재하는지 확인
        """
        if not isinstance(places, list): return 400, 'places는 리스트 형태이어야 합니다.'  # places가 리스트 형식이 아니라면
        if not tour_id or not date or len(places) == 0: return 400, '필수 파라미터 중 일부 혹은 전체가 없습니다. tour_id, date, places를 확인해주세요.' # 파라미터를 잘못 주었을 때
        try:
            tour_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            logger.info(f'date: {date} is not date format') # 클라이언트가 잘못 요청 보낸 것이므로
            return 400, "date의 형식이 올바르지 않습니다."

        # 실제로 Travel이 존재하는지 확인합니다.
        travel = None
        try:
            travel = Travel.objects.get(id=int(tour_id), user__sub=user_sub)
        except Travel.DoesNotExist: # travel이 존재하지 않는다면
            logger.warning(f'travel id: {tour_id} is not exist in DB.')
            return 404, '해당 여행이 존재하지 않습니다.'

        end_date = datetime.datetime.strptime(str(travel.end_date), "%Y-%m-%d")
        start_date = datetime.datetime.strptime(str(travel.start_date), "%Y-%m-%d")
        if end_date < tour_date or start_date > tour_date: # tour_date가 등록된 여행 날짜 외라면
            logger.warning(f'등록 범위 외 날짜 여행 등록 시도')
            return 400, '해당 여행은 등록된 날짜의 여행 날짜 범위 외 날짜 입니다.'
        return 200, 'Validate'

    def create(self, request, *args, **kwargs):  # 여행 경로 저장 API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기

        # request.data를 변경 가능한 딕셔너리로 변환
        # 필수 파라미터 추출
        course_data = request.data.copy()
        tour_id = course_data.get('tour_id', None) # 여행 id
        date = course_data.get('date', None) # 여행 날짜
        places = course_data.get('places', []) # 장소 정보들 가져오기

        # 파라미터 validate
        status_code, message = self.__validate_parameters_in_post(tour_id, date, places, user_sub)
        if status_code != 200:
            return Response({
                "error": status_code,
                "message": message
            }, status=status_code)

        travel = Travel.objects.get(id=int(tour_id), user__sub=user_sub)

        place_results = []

        for place_data in places:
            name = place_data.get('name', None)
            mapX = place_data.get('mapX', None)
            mapY = place_data.get('mapY', None)
            image_url = place_data.get('image_url', None)
            road_address = place_data.get('road_address', None) # 도로명 주소를 받아옵니다.
            parcel_address = None # 지번 주소를 받아옵니다.

            # 장소 필수 정보 누락 시 해당 장소는 스킵
            if not name or not mapX or not mapY:
                logger.info(f'필수 정보 누락 (place name: {name}, mapX: {mapX}, mapY: {mapY})') # 클라이언트 잘못이므로 info
                continue

            # 장소 저장 (중복 시 get)
            place_service = PlaceService(service_key=KAKAO_REST_API_KEY)
            if road_address is None: parcel_address, road_address = place_service.get_parcel_and_road_address(float(mapX), float(mapY))
            else: parcel_address = place_service.get_parcel(float(mapX), float(mapY))
            place, _ = Place.objects.get_or_create(
                name=name,
                mapX=mapX,
                mapY=mapY,
                road_address=road_address,
                address=parcel_address
            )

            # 날짜별 장소 연결 저장
            tdp, _ = TravelDaysAndPlaces.objects.get_or_create(
                travel=travel,
                place=place,
                date=date
            )

            # 이미지가 있을 경우 별도 저장
            if image_url:
                PlaceImages.objects.get_or_create(
                    place=place,
                    image_url=image_url
                )

            place_results.append({
                "name": name,
                "mapX": mapX,
                "mapY": mapY,
                "image_url": image_url,
                "road_address": road_address,
                "parcel_address": parcel_address,
                'place_id': place.id,
                'tdp_id': tdp.id,
            })

        # 최종 응답 반환
        return Response({
            "date": date,
            "places": place_results
        }, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):  # 여행 경로 가져오기 API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기
        tour_id = pk

        # 여행 존재 여부 및 권한 확인
        try:
            travel = Travel.objects.get(id=int(tour_id), user__sub=user_sub)
        except Travel.DoesNotExist:
            logger.warning(f'travel id: {tour_id} && sub: {user_sub} is not exist in DB.')
            return Response({
                "error": "403",
                "message": "해당 여행이 존재하지 않거나 접근 권한이 없습니다."
            }, status=status.HTTP_403_FORBIDDEN)

        # 해당 여행에 연결된 날짜별 장소 정보 조회
        travel_days = TravelDaysAndPlaces.objects.filter(travel=travel).order_by('date')
        if not travel_days.exists():
            logger.warning(f'travel id: {tour_id} && sub: {user_sub} has no travel days.')
            return Response({
                "message": "저장된 여행 경로 정보가 없습니다.",
                "tour_id": tour_id,
                "courses": []
            }, status=status.HTTP_200_OK)

        result = {}  # date 별로 그룹화

        for entry in travel_days:
            date_str = str(entry.date)

            if date_str not in result:
                result[date_str] = []

            image_url = ""
            image_obj = PlaceImages.objects.filter(place=entry.place).first()
            if image_obj:
                image_url = image_obj.image_url

            result[date_str].append({
                "name": entry.place.name,
                "mapX": entry.place.mapX,
                "mapY": entry.place.mapY,
                "image_url": image_url,
                "road_address": entry.place.road_address,
                "parcel_address": entry.place.address,
                "place_id": entry.place.id,
                "tdp_id": entry.id,
            })

        # 응답 형태: [{ "date": "YYYY-MM-DD", "places": [...] }, ...]
        response_data = [
            {
                "date": date,
                "places": places
            } for date, places in result.items()
        ]

        return Response(response_data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None):
        user_sub = request.user.sub  # 로그인한 사용자의 sub
        tour_id = pk  # URL에서 받은 여행 ID
        del_date = request.data.get('target_date', None)
        if not del_date:
            raise NoRequiredParameterException()
        try:
            tour_date = datetime.datetime.strptime(del_date, "%Y-%m-%d")
        except ValueError:
            raise ValueException(
                error_message=f'date: {del_date} is not date format'
            )


        instances = TravelDaysAndPlaces.objects.filter(travel__id=int(tour_id), date=tour_date)
        if not instances.exists():
            logger.warning(f'travel id: {tour_id} && sub: {user_sub} has no travel days.')
            raise NoObjectException(
                'No Object exists.',
                f'해당 날짜의 여행이 존재하지 않습니다.'
            )
        instances.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def list(self, request, *args, **kwargs):  # 여행 경로 리스트 조회 API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기

        # 사용자가 해당하는 여행 경로들을 모두 조회
        try:
            travels = Travel.objects.filter(user__sub=user_sub)  # 해당 user의 여행 경로들
        except Travel.DoesNotExist:
            raise NoObjectException(
                'No Travel object exists.',
                f'sub: {user_sub}의 여행이 존재하지 않습니다.'
            )

        # 여행 경로들에 대한 결과 리스트 생성
        travel_results = []

        for travel in travels:
            # 여행 경로에 포함된 장소들 조회
            travel_days_and_places = TravelDaysAndPlaces.objects.filter(travel=travel)

            # 장소 리스트 생성
            places = []
            for travel_day_place in travel_days_and_places:
                place = travel_day_place.place
                places.append({
                    "name": place.name,
                    "mapX": place.mapX,
                    "mapY": place.mapY,
                    "image_url": place.placeimages_set.first().image_url if place.placeimages_set.exists() else None
                })

            # 여행 경로 데이터 포맷
            travel_results.append({
                "tour_id": travel.id,
                "tour_name": travel.tour_name,
                "start_date": str(travel.start_date),
                "end_date": str(travel.end_date),
                "places": places
            })

        # 최종 응답 반환
        return Response({
            "travels": travel_results
        }, status=status.HTTP_200_OK)

