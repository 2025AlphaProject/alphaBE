from django.urls import path
from tour.consumers import TaskConsumer

websocket_urlpatterns = [
    path("ws/task/<str:task_id>/", TaskConsumer.as_asgi()),
]