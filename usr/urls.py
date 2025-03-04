from django.contrib import admin
from django.urls import path, include  # include() 추가

urlpatterns = [
    path('admin/', admin.site.urls),
    path('usr/', include('usr.urls')),  # usr 앱의 urls.py 포함
]
