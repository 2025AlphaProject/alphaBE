from django.urls import path
from .views import Who

urlpatterns = [
    path('me/',Who.as_view({
        'get' : 'retrieve',
    }), name='who'),
]