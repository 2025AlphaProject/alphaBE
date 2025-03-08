from django.urls import path
from .views import TravelViewSet

urlpatterns = [

    path('user/tour/', TravelViewSet.as_view({
        'post': 'create'}),
         name='travel-create'),


    path('user/tour/', TravelViewSet.as_view({
        'get': 'list'}),
         name='travel-list'),


    path('user/tour/<int:pk>/', TravelViewSet.as_view({
        'get': 'retrieve'}),
         name='travel-detail'),


    path('user/tour/<int:pk>/', TravelViewSet.as_view({
        'put': 'update'}),
         name='travel-update'),


    path('user/tour/<int:pk>/', TravelViewSet.as_view({
        'delete': 'destroy'}),
         name='travel-delete'),
]
