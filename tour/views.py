from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Travel
from .serializers import TravelSerializer

class TravelViewSet(viewsets.ModelViewSet):
    queryset = Travel.objects.all()
    serializer_class = TravelSerializer

    def create(self, request, *args, **kwargs):  # 새로운 여행 등록 API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기

        # request.data를 변경 가능한 딕셔너리로 변환 후 user 추가
        travel_data = dict(request.data).copy()
        travel_data["user"] = user_sub

        serializer = self.get_serializer(data=travel_data)  # 수정된 데이터로 serializer 초기화

        if serializer.is_valid():  # 데이터에 모든 필드가 다 있을 때 실행되는 조건문
            travel = serializer.save()  # ORM을 이용해 저장

            # json 응답을 반환
            return Response({
                "tour_id": travel.id,
                "tour_name": travel.tour_name,
                "start_date": str(travel.start_date),
                "end_date": str(travel.end_date)
            }, status=status.HTTP_201_CREATED)

        # 데이터가 일부 누락되었을 때
        return Response({
            "error": "400",
            "message": "필수 파라미터 중 일부 혹은 전체가 없습니다. 필수 파라미터 목록을 확인해주세요"
        }, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):  # 리스트 조회 API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기
        queryset = self.get_queryset().filter(user_id=user_sub)  # 로그인한 사용자의 여행만 조회
        serializer = self.get_serializer(queryset, many=True)

        # json 응답을 반환
        response_data = [
            {
                "tour_id": travel["id"],
                "tour_name": travel["tour_name"],
                "start_date": travel["start_date"],
                "end_date": travel["end_date"]
            } for travel in serializer.data
        ]

        return Response(response_data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):  # 내 여행 가져오기(하나만) API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기
        tour_id = kwargs.get('pk')

        try:
            travel = Travel.objects.get(id=tour_id, user_id=user_sub)  # 로그인한 사용자의 여행인지 확인
        except Travel.DoesNotExist:
            return Response({
                "error": "404",
                "message": "해당 여행 ID가 존재하지 않거나, 접근 권한이 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "tour_id": travel.id,
            "tour_name": travel.tour_name,
            "start_date": str(travel.start_date),
            "end_date": str(travel.end_date)
        }, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):  # 여행 정보 수정 API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기
        tour_id = kwargs.get('pk')

        try:
            travel = Travel.objects.get(id=tour_id, user_id=user_sub)  # 로그인한 사용자의 여행인지 확인
        except Travel.DoesNotExist:
            return Response({
                "error": "404",
                "message": "해당 여행 ID가 존재하지 않거나, 접근 권한이 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)

        data = request.data  # 수정할 데이터 가져오기

        if "tour_name" in data:
            travel.tour_name = data["tour_name"]
        if "start_date" in data:
            travel.start_date = data["start_date"]
        if "end_date" in data:
            travel.end_date = data["end_date"]

        travel.save()  # 변경 사항 저장

        return Response({
            "tour_id": travel.id,
            "tour_name": travel.tour_name,
            "start_date": str(travel.start_date),
            "end_date": str(travel.end_date)
        }, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):  # 여행 삭제 API
        user_sub = request.user.sub  # 액세스 토큰에서 sub 값 가져오기
        tour_id = kwargs.get('pk')

        try:
            travel = Travel.objects.get(id=tour_id, user_id=user_sub)  # 로그인한 사용자의 여행인지 확인
        except Travel.DoesNotExist:
            return Response({
                "error": "404",
                "message": "해당 여행 ID가 존재하지 않거나, 접근 권한이 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)

        travel.delete()  # 여행 데이터 삭제
        return Response(status=status.HTTP_204_NO_CONTENT)  # 204 No Content 응답 반환
