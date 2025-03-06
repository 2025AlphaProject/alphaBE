from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Travel
from .serializers import TravelSerializer

class TravelViewSet(viewsets.ModelViewSet):
    queryset = Travel.objects.all()
    serializer_class = TravelSerializer

    def create(self, request, *args, **kwargs): # 새로운 여행 등록
        serializer = self.get_serializer(data=request.data)

        #데이터에 모든 필드가 다 있을 때 실행되는 ㅈ건문
        if serializer.is_valid():
            travel = serializer.save() #travel 모델에 데이터 저장

            #json 응답을 반환
            return Response({
                "tour_id": travel.id,
                "tour_name": travel.tour_name,
                "start_date": str(travel.start_date),
                "end_date": str(travel.end_date)
            }, status=status.HTTP_201_CREATED)

        #데이터 좀 누락되었을 때
        return Response({
            "error": "400",
            "message": "필수 파라미터 중 일부 혹은 전체가 없습니다. 필수 파라미터 목록을 확인해주세요"
        }, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):  # 리스트 조회 API
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        response_data = [
            {
                "tour_id": travel["id"],
                "tour_name": travel["tour_name"],
                "start_date": travel["start_date"],
                "end_date": travel["end_date"]
            } for travel in serializer.data
        ]

        return Response(response_data, status=status.HTTP_200_OK)