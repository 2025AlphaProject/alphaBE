from django.contrib import admin
from .models import Place, Travel, TravelDaysAndPlaces, PlaceImages, Event

# Register your models here.
admin.site.register(Place) # 장소 정보 관리자가 관리 가능하도록 함
admin.site.register(Travel)
admin.site.register(TravelDaysAndPlaces)
admin.site.register(PlaceImages)
admin.site.register(Event)