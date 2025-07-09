from django.urls import path
from .views import MissionListView, MissionImageUploadView, RandomMissionCreateView, MissionCheckCompleteView, IsMissionCompleteView, MissionImageGetView, SaveMissionCompleteView

urlpatterns = [
    path('list/', MissionListView.as_view({
        'get': 'list', # get 메소드에만 매핑합니다.
    }), name='mission_list'),

    path('image_upload/', MissionImageUploadView.as_view({
        'post': 'create',
    }), name='mission_image_upload'),

    path('random/',RandomMissionCreateView.as_view({
        'post': 'create',
    }), name = 'mission_random_create'),
    path('check_complete/', MissionCheckCompleteView.as_view({
        'post': 'create',  # 사진을 올리고 검사를 받는 로직 구성
    }), name='mission_check'),
    path('is_complete/<int:pk>/', IsMissionCompleteView.as_view({
        'get': 'retrieve',
    })),
    path('get_mission_img/<int:pk>/', MissionImageGetView.as_view({
        'get': 'retrieve',
    })),
    path('save_mission_complete/', SaveMissionCompleteView.as_view({
        'post': 'create',
    }))
]