from django.urls import path
from .views import MissionListView, MissionCheckCompleteView

urlpatterns = [
    path('list/', MissionListView.as_view({
        'get': 'list', # get 메소드에만 매핑합니다.
    }), name='mission_list'),
    path('check_complete/', MissionCheckCompleteView.as_view({
        'post': 'create', # 사진을 올리고 검사를 받는 로직 구성
    }))
]