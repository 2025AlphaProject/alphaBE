from django.contrib import admin
from .models import Mission

# Register your models here.
admin.site.register(Mission) # 미션을 추가함으로써 장고 관리자 화면에서 미션을 임의로 추가할 수 있도록 합니다.