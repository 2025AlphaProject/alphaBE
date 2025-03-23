from django.urls import path
from .views import kakao_callback, KakaoRefreshTokens, LoginRegisterView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', LoginRegisterView.as_view({
        'post': 'create',
    }), name='login_register'),
    path('get_token/', kakao_callback, name='login'), # 로그인 url 매핑
    path('refresh/', TokenRefreshView.as_view(), name='refresh_tokens'),
]