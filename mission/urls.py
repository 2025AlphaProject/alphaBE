from django.urls import path
from .views import MissionListView, MissionImageUploadView, RandomMissionCreateView

urlpatterns = [
    path('list/', MissionListView.as_view({
        'get': 'list', # get 메소드에만 매핑합니다.
    }), name='mission_list'),

    path('image_upload/', MissionImageUploadView.as_view({
        'post': 'create',
    }), name='mission_image_upload'),

    path('random/',RandomMissionCreateView.as_view({
        'post': 'create',
    }), name = 'mission_random_create')
]