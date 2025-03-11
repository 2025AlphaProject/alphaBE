from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Mission, TestMission
from .serializers import MissionSerializer
from tour.models import TravelDaysAndPlaces


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
        travel_days_and_places.image = image
        travel_days_and_places.save()
        return Response({"message": "image upload success"}, status=status.HTTP_201_CREATED)


class MissionCheckCompleteView(viewsets.ModelViewSet):
    """
    Handles operations related to completing mission checks within the system.

    This class extends `viewsets.ModelViewSet` and is responsible for providing
    create, retrieve, update, and delete operations for mission check completion.
    It is tightly integrated with Django REST Framework and offers functionalities
    to manage mission check statuses effectively.

    Attributes:
        queryset: The default QuerySet used to retrieve objects. Typically, this is
            set to MissionCheckComplete.objects.all() or similar to include all
            mission completion records.
        serializer_class: The serializer class used to convert query objects into
            native Python data types and vice versa. This serializer handles
            validation and data transformation.
        permission_classes: List of permission classes that specify the access
            controls. This typically ensures only authorized users can perform
            operations on mission check data.

    """
    pass