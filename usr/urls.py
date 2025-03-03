from django.urls import path
from .views import Who

urlpatterns = [
    path("who/", Who.as_view(), name="who"),
]
