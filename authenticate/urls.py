from django.urls import path
from .views import kakao_callback, KakaoRefreshTokens

urlpatterns = [
    path('login/', kakao_callback, name='kakao_login'), # 로그인 url 매핑
    path('refresh/', KakaoRefreshTokens.as_view({
        'post': 'create' # post 메소드를 클래스 내 create로 매핑
    }), name='kakao_refresh_tokens'),
]