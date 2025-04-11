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


class MissionCheckCompleteView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """
        사용자가 업로드한 이미지와 장소 예시 이미지를 비교해
        미션 성공 여부를 판단하고 응답합니다.
        """
        travel_id = request.data.get('travel_id')
        place_id = request.data.get('place_id')
        mission_id = request.data.get('mission_id')

        # 필수값 누락 체크
        if not travel_id or not place_id or not mission_id:
            return Response({"error": "travel_id, place_id, mission_id는 필수입니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 이미지 유사도 비교 클래스 생성
            checker = ImageSimilarity(travel_id, place_id, mission_id)
            result = checker.check_mission_success()  # 1: 성공, 0: 실패
            score = checker.get_similarity_score()    # 유사도 점수

            return Response({
                "result": "success" if result == 1 else "fail",
                "similarity_score": score,
                "message": "미션 판별 완료"
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)