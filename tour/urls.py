from django.urls import path
from .views import TravelViewSet, NearEventView, AddTravelerView

urlpatterns = [
    path('', TravelViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='travel-list-create'),

    path('<int:pk>/', TravelViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    }), name='travel-detail'),
    path('near_event/', NearEventView.as_view({
        'get': 'list',
    }), name='near_event'), # 주변 행사 정보 url 매핑
    path('add_traveler/', AddTravelerView.as_view({
        'post': 'create'
    }), name='add_traveler')
]
