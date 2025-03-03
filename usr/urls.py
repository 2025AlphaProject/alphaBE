from django.urls import path
from .views import Who

urlpatterns = [
    path('user/me/', Who.as_view(), name='user_me'),
]
