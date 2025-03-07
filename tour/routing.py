from django.urls import path
from tour.consumers import TaskConsumer

websocket_urlpatterns = [
    path("tour/recommend/", TaskConsumer),
]