from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Mission
from .serializers import MissionSerializer
from tour.models import TravelDaysAndPlaces, Place
from .services import ImageSimilarity


# Create your views here.
class MissionListView(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer

class MissionImageUploadView(viewsets.ModelViewSet):
    """
    여행 일차별 방문 장소 id를 받습니다.
    """
    # permission_classes = [IsAuthenticated] # 로그인 한 사용자만
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


class MissionCheckCompleteView(viewsets.ModelViewSet):
    """
    미션 성공 여부를 확인하는 API 입니다.
    """
    # permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        여행 ID, 장소 ID, 미션 ID를 받아서 미션 성공 여부를 반환합니다.
        """
        travel_days_id = request.data.get("travel_days_id", None)
        place_id = request.data.get("place_id", None)
        mission_id = request.data.get("mission_id", None)

        # 필수 값이 없으면 400 에러 반환
        if travel_days_id is None or place_id is None or mission_id is None:
            return Response({"Error": "travel_days_id, place_id, or mission_id is missing"},
                            status=status.HTTP_400_BAD_REQUEST)

        # TravelDaysAndPlaces 객체 확인 (미션 사진이 있는지)
        try:
            travel_day = TravelDaysAndPlaces.objects.get(id=travel_days_id, mission=mission_id)
        except TravelDaysAndPlaces.DoesNotExist:
            return Response({"Error": "Invalid travel_days_id or mission_id"}, status=status.HTTP_404_NOT_FOUND)

        # Place 객체 확인 (장소 예시 이미지가 있는지)
        try:
            place_id = Place.objects.get(id=place_id)
        except Place.DoesNotExist:
            return Response({"Error": "Invalid place_id"}, status=status.HTTP_404_NOT_FOUND)

        # 이미지 비교 수행
        similarity_checker = ImageSimilarity(travel_day.id, place_id, mission_id)
        similarity_score = similarity_checker.get_similarity_score()
        mission_success = similarity_checker.check_mission_success()


        return Response({
            "message": "Mission check complete",
            "similarity_score": similarity_score,
            "mission_success": mission_success
        }, status=status.HTTP_200_OK)