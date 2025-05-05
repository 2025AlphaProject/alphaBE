from django.urls import path
from .views import TravelViewSet, NearEventView, AddTravelerView, GetAreaList, Sido_list, CourseView

urlpatterns = [
    path('', TravelViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='travel-list-create'),

    path('<int:pk>/', TravelViewSet.as_view({
        'get': 'retrieve',
        'put': 'partial_update',
        'delete': 'destroy'
    }), name='travel-detail'),

    path('near_event/', NearEventView.as_view({
        'get': 'list',
    }), name='near_event'),

    path('add_traveler/', AddTravelerView.as_view({
        'post': 'create'
    }), name='add_traveler'),

    path('get_area_list/', GetAreaList.as_view({
        'get': 'list',
    }), name='get_area_list'),

    path('get_sido_list/', Sido_list.as_view({
        'get': 'retrieve'
    })),

    path('course/', CourseView.as_view({
        'post': 'create',   # 저장
        'get': 'list'       # 전체 조회
    }), name='course-list-create'),

    path('course/<int:pk>/', CourseView.as_view({
        'get': 'retrieve',  # 개별 조회
        'delete': 'destroy' # 삭제
    }), name='course-detail'),

]
