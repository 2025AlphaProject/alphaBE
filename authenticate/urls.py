from django.urls import path
from .views import kakao_callback

urlpatterns = [
    path('login/', kakao_callback, name='kakao_login'), # 로그인 url 매핑
]