from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Mission
from .serializers import MissionSerializer
from tour.models import TravelDaysAndPlaces, Place

import random


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

class RandomMissionCreateView(viewsets.ModelViewSet):
    """
    이미지가 없는 장소(place)에 대해 임의의 미션을 생성합니다.
    프론트에서 이미지 링크가 빈 문자열("")로 들어오는 장소만 처리 대상입니다.
    """
    permission_classes = [IsAuthenticated]  # 인증된 사용자만

    # 임의 미션 문구 리스트
    RANDOM_MISSIONS = [
        "근처 구조물과 함께 사진 찍기",
        "간판이 보이도록 찍어주세요!",
        "이 장소의 전경이 나오도록 찍어보세요",
        "내가 방문한 인증샷 남기기",
        "해당 위치의 분위기를 담아보세요"
    ]

    def create(self, request, *args, **kwargs):
        """
        POST 요청 시 빈 이미지 링크("")를 가진 장소들을 필터링하여
        랜덤한 미션을 각 장소에 생성해주는 로직입니다.
        """
        places = request.data.get("places", [])
        if not isinstance(places, list):
            return Response({
                "error": "places 필드는 리스트여야 합니다."
            }, status=status.HTTP_400_BAD_REQUEST)

        created_missions = []

        for item in places:
            place_id = item.get("place_id")
            image_url = item.get("image_url", "")

            # 빈 이미지 문자열인 경우만 처리
            if image_url == "":
                try:
                    place = Place.objects.get(id=place_id)
                except Place.DoesNotExist:
                    continue  # 잘못된 장소 ID는 무시하고 진행

                # 랜덤 미션 생성 및 저장
                mission_text = random.choice(self.RANDOM_MISSIONS)
                mission = Mission.objects.create(content=mission_text)

                # 여기선 연결만 해주고, 나중에 TravelDaysAndPlaces에서 연결해도 OK
                created_missions.append({
                    "place_id": place_id,
                    "mission_content": mission.content,
                    "mission_id": mission.id
                })

        return Response({
            "message": "랜덤 미션 생성 완료",
            "missions": created_missions
        }, status=status.HTTP_201_CREATED)