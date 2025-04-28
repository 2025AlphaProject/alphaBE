from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Mission
from .serializers import MissionSerializer
from tour.models import TravelDaysAndPlaces, Place
from .services import ImageSimilarity, ObjectDetection
import random
from tour.services import NearEventInfo

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
        """
        사용자의 GPS(mapX, mapY)와
        1) 원래 사진이 있는 경우 → 이미지 유사도
        2) 사진이 없는 임의 미션인 경우 → 객체 인식
        을 통해 미션 성공 여부를 판별하는 API입니다.
        """

        travel_id = request.data.get('travel_id')
        place_id = request.data.get('place_id')
        mission_id = request.data.get('mission_id')
        user_lng = request.data.get('mapX')  # 경도
        user_lat = request.data.get('mapY')  # 위도

        # 필수값 누락 검사
        if not travel_id or not place_id or not mission_id or not user_lat or not user_lng:
            return Response({"error": "필수 입력값이 누락되었습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            place = Place.objects.get(id=place_id)
            travel_place = TravelDaysAndPlaces.objects.get(place=place)

            # 위도, 경도 float 변환
            place_lat = float(place.mapY)
            place_lng = float(place.mapX)
            user_lat = float(user_lat)
            user_lng = float(user_lng)

            # 거리 계산 (NearEventInfo 모듈 사용)
            distance = NearEventInfo.haversine(user_lat, user_lng, place_lat, place_lng)
            location_pass = distance <= 200.0  # 200m 이내

            # 원래 사진(mission_image)이 있는지 없는지 확인
            if travel_place.mission_image:
                # 원본 사진 존재 → 유사도 검사
                checker = ImageSimilarity(travel_id, place_id, mission_id)
                similarity_score = checker.get_similarity_score()
                image_pass = similarity_score >= 40.0
                method = "image_similarity"

            else:
                # 원본 사진 없음 (임의 미션) → YOLO 객체 인식
                detector = ObjectDetection()
                mission_content = travel_place.mission.content  # 할당된 임의 미션 내용
                uploaded_image_path = travel_place.mission_image.path  # 업로드된 인증 사진 경로

                image_pass = detector.detect_and_check(uploaded_image_path, mission_content)
                similarity_score = None  # YOLO 기반 판별이므로 유사도 없음
                method = "object_detection"

            # 최종 미션 성공 여부
            is_success = location_pass and image_pass

            return Response({
                "result": "success" if is_success else "fail",
                "distance_to_place": round(distance, 2),
                "image_check_passed": image_pass,
                "location_check_passed": location_pass,
                "similarity_score": similarity_score,  # (YOLO 기반이면 None)
                "method_used": method,  # 어떤 방식으로 판별했는지: image_similarity / object_detection
                "message": "미션 판별 완료"
            }, status=status.HTTP_200_OK)

        except Place.DoesNotExist:
            return Response({"error": "place_id가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
        except TravelDaysAndPlaces.DoesNotExist:
            return Response({"error": "여행지 정보가 존재하지 않습니다."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({"error": "mapX, mapY는 유효한 float 값이어야 합니다."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"서버 오류: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RandomMissionCreateView(viewsets.ViewSet):
    """
    이미지가 없는 장소(place)에 대해 미리 등록된 Mission 중 랜덤으로 할당합니다.
    TravelDaysAndPlaces에 mission 필드를 설정합니다.
    """
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        places = request.data.get("places", [])
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
            place_id = item.get("place_id")
            image_url = item.get("image_url", "")

            if image_url == "":
                try:
                    place = Place.objects.get(id=place_id)
                    tdp = TravelDaysAndPlaces.objects.get(place=place)

                    if tdp.mission is not None:
                        continue  # 이미 미션이 있으면 건너뜀

                    selected_mission = random.choice(missions_queryset)
                    tdp.mission = selected_mission
                    tdp.save()

                    created_missions.append({
                        "place_id": place_id,
                        "mission_id": selected_mission.id,
                        "mission_content": selected_mission.content,
                    })

                except (Place.DoesNotExist, TravelDaysAndPlaces.DoesNotExist):
                    continue

        return Response({
            "message": "랜덤 미션 할당 완료",
            "missions": created_missions
        }, status=status.HTTP_201_CREATED)