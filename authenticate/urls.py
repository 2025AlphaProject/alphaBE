from django.urls import path
from .views import kakao_callback, KakaoRefreshTokens, IssueTokenView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('login/', IssueTokenView.as_view(), name='login'), # 로그인 url 매핑
    path('refresh/', TokenRefreshView.as_view(), name='refresh_tokens'),
]