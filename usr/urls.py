from django.urls import path
from .views import Who

urlpatterns = [
    path('me/',Who.as_view(), name='who'),
]