from django.urls import path
from .views import TravelViewSet

urlpatterns = [
    path('user/tour/', TravelViewSet.as_view({
        'post': 'create'}),
         name='travel-create'),
]
