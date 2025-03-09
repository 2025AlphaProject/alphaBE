from config.settings import SEOUL_PUBLIC_DATA_SERVICE_KEY
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import EventSerializer
from .modules.tour_api import NearEventInfo

from .models import Event

# Create your views here.
class NearEventView(viewsets.ModelViewSet):
    serializer_class =  EventSerializer# 이벤트 시리얼라이저 GET
    queryset = Event.objects.all() # 이벤트 모델 GET

    def list(self, request, *args, **kwargs):
        """
        해당 함수는 tour_api의 NearEventInfo 클래스를 통해 얻어온 주변 정보를 바탕으로 주변 문화 정보를 반환해줍니다.
        """
        mapX = float(request.GET.get('mapX', None))
        mapY = float(request.GET.get('mapY', None))
        if mapX is None or mapY is None: # 필수 파라미터 검증
            return Response({"ERROR": "필수 파라미터 중 일부 혹은 전체가 없습니다."}, status=status.HTTP_400_BAD_REQUEST)
        if Event.objects.count() == 0:
            return Response({"Message": "주변 행사 정보 데이터가 서버 내에 없습니다."}, status=status.HTTP_200_OK)

        event_info = NearEventInfo(Event, SEOUL_PUBLIC_DATA_SERVICE_KEY, Event.objects.all())
        events = event_info.get_near_by_events(mapY, mapX) # 주변 행사 정보를 불러옵니다.
        serializer = self.get_serializer(events, many=True) # 시리얼라이저에 정보를 넣어 시리얼라이징합니다.
        return Response(serializer.data, status=status.HTTP_200_OK)