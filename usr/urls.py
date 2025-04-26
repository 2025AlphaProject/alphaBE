from django.urls import path
from .views import Who, UserListView

urlpatterns = [
    path('', UserListView.as_view({
        'get' : 'list',
    }), name='user_list'), # 유저 리스트 뷰 매핑
    path('me/',Who.as_view({
        'get' : 'retrieve',
    }), name='who'), # 토큰 이용한 내 정보 get 매핑
]