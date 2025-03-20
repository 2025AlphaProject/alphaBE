from django.urls import path
from .views import Who, UserListView

urlpatterns = [
    path('', UserListView.as_view({
        'get' : 'list',
    }), name='user_list'),
    path('me/',Who.as_view({
        'get' : 'retrieve',
    }), name='who'),
]