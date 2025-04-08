from django.urls import path
from .views import TravelViewSet, NearEventView, AddTravelerView, GetAreaList, Sido_list, CourseListView

urlpatterns = [
    path('', TravelViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='travel-list-create'),

    path('<int:pk>/', TravelViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    }), name='travel-detail'),
    path('near_event/', NearEventView.as_view({
        'get': 'list',
    }), name='near_event'),  # 주변 행사 정보 url 매핑
    path('add_traveler/', AddTravelerView.as_view({
        'post': 'create'
    }), name='add_traveler'),  # 여행자 추가 url 매핑
    path('get_area_list/', GetAreaList.as_view({
        'get': 'list',
    }), name='get_area_list'),
    path('get_sido_list/', Sido_list.as_view({
        'get': 'retrieve'
    }), name='get_sido_list'),  # 시도 목록

    path('course/list/', CourseListView.as_view({
        'get': 'list'
    }), name='tour-course-list'),  # 여행 경로 리스트 조회

]
