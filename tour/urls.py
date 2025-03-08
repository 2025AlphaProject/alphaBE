from django.urls import path
from .views import NearEventView

urlpatterns = [
    path('near_event/', NearEventView.as_view({
        'get': 'list',
    }), name='near_event'), # 주변 행사 정보 url 매핑
]