from django.urls import path
from .views import TravelViewSet

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
]
