from django.urls import path

from .views import (
    NearEventView,
    AddTravelerView,
    GetAreaList,
    Sido_list,
    NewTourAddView,
    TourSnapshotsView,
    CategoryListView, UserTourImageView,
    Category2ListView
)

urlpatterns = [
    path('', NewTourAddView.as_view({
        'get': 'list',
        'post': 'create'
    }), name='create-tour'),

    path('<int:pk>/', NewTourAddView.as_view({
        'get': 'retrieve',
        'patch': 'partial_update', # 메소드를 일부 업데이트인 patch로 변경
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
    path('snapshot/', TourSnapshotsView.as_view({
        'get': 'list',
        'post': 'create',
    })),
    path('snapshot/<int:pk>/', TourSnapshotsView.as_view({
        'get': 'retrieve',
        'delete': 'destroy',
    })),

    path('category/', CategoryListView.as_view({
        'get': 'retrieve'  # 카테고리 리스트 조회
    }), name='category-list'),
    path('image/', UserTourImageView.as_view({
        'get': 'list',
        'post': 'create',
    })),
    path('image/<int:pk>/', UserTourImageView.as_view({
        'get': 'retrieve',
        'delete': 'destroy'
    })),
    path('category2',Category2ListView.as_view({
        'get' : 'retrieve'
    }), name='category2-list')
]
