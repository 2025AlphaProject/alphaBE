from django.urls import path
from .views import MissionListView

urlpatterns = [
    path('list/', MissionListView.as_view({
        'get': 'list', # get 메소드에만 매핑합니다.
    }), name='mission_list'),
]