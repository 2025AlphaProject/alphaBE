from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Mission
from .serializers import MissionSerializer
from tour.models import TravelDaysAndPlaces, Place, PlaceImages
from .services import ImageSimilarity, ObjectDetection
import random
from services.tour_api import NearEventInfo
import requests
import tempfile
import traceback

# Create your views here.
class MissionListView(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer

class MissionImageUploadView(viewsets.ModelViewSet):
    """
    여행 일차별 방문 장소 id를 받습니다.
    """
    permission_classes = [IsAuthenticated] # 로그인 한 사용자만
    def create(self, request, *args, **kwargs):
        """
        post 요청시 들어오는 함수입니다. 여행 일차별 방문 장소 id와 이미지를 받습니다.
        """
        travel_days_and_places_id = request.data.get('travel_days_id', None)
        image = request.FILES.get('image', None)
        if travel_days_and_places_id is None or image is None:
            return Response({"Error": "travel_days_and_places_id or image is missing"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            travel_days_and_places = TravelDaysAndPlaces.objects.get(id=travel_days_and_places_id)
        except TravelDaysAndPlaces.DoesNotExist:
            return Response({"Error": "travel_days_id is not exist"}, status=status.HTTP_404_NOT_FOUND)
        travel_days_and_places.mission_image = image
        travel_days_and_places.save()
        return Response({
            "message": "image upload success",
            'mission_image_url': travel_days_and_places.mission_image.url, # aws url 형식으로 줍니다.
        }, status=status.HTTP_201_CREATED)


class MissionCheckCompleteView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        travel_id = request.data.get('travel_id')
        place_id = request.data.get('place_id')
        mission_id = request.data.get('mission_id')  # object_detection용일 경우 필요
        user_lng = request.data.get('mapX')
        user_lat = request.data.get('mapY')

        if not travel_id or not place_id or not user_lat or not user_lng:
            return Response({"error": "필수 입력값이 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            place = Place.objects.get(id=place_id)
            travel_place = TravelDaysAndPlaces.objects.get(place=place, travel_id=travel_id)

            place_lat = float(place.mapY)
            place_lng = float(place.mapX)
            user_lat = float(user_lat)
            user_lng = float(user_lng)

            # 거리 계산
            distance = NearEventInfo.haversine(user_lat, user_lng, place_lat, place_lng)
            location_pass = distance <= 0.2

            # 이미지 비교 방식 결정
            has_original_image = PlaceImages.objects.filter(place=place).exists()

            if has_original_image:
                # ✅ 추천 장소 → 유사도 기반 판별, mission_id 없어도 됨
                checker = ImageSimilarity(travel_id, place_id,mission_id)
                similarity_score = checker.get_similarity_score()
                image_pass = similarity_score >= 40.0
                method = "image_similarity"
            else:
                # ✅ 랜덤 미션 장소 → 객체 인식 기반 판별, mission_id 필수
                if not mission_id:
                    raise ValueError("랜덤 미션 판별에는 mission_id가 필요합니다.")

                detector = ObjectDetection()
                mission_content = travel_place.mission.content

                if not travel_place.mission_image:
                    raise ValueError("업로드된 이미지가 없습니다.")

                # S3 이미지 다운로드 후 임시 파일로 저장
                image_url = travel_place.mission_image.url
                with requests.get(image_url, stream=True) as r:
                    if r.status_code != 200:
                        raise ValueError("이미지를 불러올 수 없습니다.")

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                        for chunk in r.iter_content(chunk_size=8192):
                            tmp.write(chunk)
                        tmp_path = tmp.name

                image_pass = detector.detect_and_check(tmp_path, mission_content)
                similarity_score = None
                method = "object_detection"

            is_success = location_pass and image_pass

            return Response({
                "result": "success" if is_success else "fail",
                "distance_to_place": round(distance, 2),
                "image_check_passed": image_pass,
                "location_check_passed": location_pass,
                "similarity_score": similarity_score,
                "method_used": method,
                "message": "미션 판별 완료"
            }, status=status.HTTP_200_OK)

        except Place.DoesNotExist:
            return Response({"error": "place_id가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
        except TravelDaysAndPlaces.DoesNotExist:
            return Response({"error": "여행지 정보가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            traceback.print_exc()
            return Response({"error": f"서버 내부 오류: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RandomMissionCreateView(viewsets.ViewSet):
    """
    이미지가 없는 장소(place)에 대해 미리 등록된 Mission 중 랜덤으로 할당합니다.
    TravelDaysAndPlaces에 mission 필드를 설정합니다.
    """
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        places = request.data.get("places", None)
        if not isinstance(places, list):
            return Response({"error": "places 필드는 리스트여야 합니다."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 관리자 등록 미션들
        missions_queryset = Mission.objects.all()
        if not missions_queryset.exists():
            return Response({"error": "Mission 테이블에 등록된 미션이 없습니다."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        created_missions = []

        for item in places:
            tdp_id = item.get("tdp_id", None)
            image_url = item.get("image_url", "")
            if tdp_id is None:
                return Response({"ERROR": "일부 파라미터에 대한 날짜 정보가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

            if image_url == "":
                try:
                    tdp = TravelDaysAndPlaces.objects.get(id=int(tdp_id))

                    if tdp.mission is not None:
                        created_missions.append({
                            "tdp_id": tdp.id,
                            "mission_id": tdp.mission.id,
                            "mission_content": tdp.mission.content,
                        })
                        continue

                    selected_mission = random.choice(missions_queryset)
                    tdp.mission = selected_mission
                    tdp.save()

                    created_missions.append({
                        "tdp_id": tdp_id,
                        "mission_id": selected_mission.id,
                        "mission_content": selected_mission.content,
                    })

                except TravelDaysAndPlaces.DoesNotExist:
                    return Response({"ERROR": "장소 정보 혹은 해당 여행 경로 정보를 불러올 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
            else:
                try:
                    tdp = TravelDaysAndPlaces.objects.get(id=tdp_id)
                    created_missions.append({
                        "place_id": tdp_id,
                        "mission_content": '예시 사진과 유사하게 찍기',
                    })
                except TravelDaysAndPlaces.DoesNotExist:
                    return Response({"ERROR": "장소 정보 혹은 해당 여행 경로 정보를 불러올 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "message": "랜덤 미션 할당 완료",
            "missions": created_missions
        }, status=status.HTTP_201_CREATED)


class IsMissionCompleteView(viewsets.ViewSet):

    def retrieve(self, request, *args, **kwargs):
        tdp = kwargs.get('pk', None)
        travel_days_and_places = None
        try:
            travel_days_and_places = TravelDaysAndPlaces.objects.get(id=tdp)
        except TravelDaysAndPlaces.DoesNotExist:
            return Response({'ERROR': '해당 여행 장소를 찾을 수 없습니다.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'tdp_id': tdp,
            'mission_success': travel_days_and_places.mission_success
        }, status=status.HTTP_200_OK)