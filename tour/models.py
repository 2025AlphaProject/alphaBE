from django.db import models
from usr.models import User

# Create your models here.

class Travel(models.Model):
    # id: pk
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 유저 제거시 해당 여행도 제거
    tour_name = models.CharField(max_length=255)  # 여행 이름 필드 추가
    start_date = models.DateField() # 여행 시작 날짜
    end_date = models.DateField() # 여행 마감 날짜

class Place(models.Model):
    # id: pk
    name = models.CharField(max_length=100) # 장소 이름, 글자 수 제한
    mapX = models.FloatField() # 소수점 표현
    mapY = models.FloatField() # 소수점 표현

class TravelDaysAndPlaces(models.Model):
    # id: pk
    travel = models.ForeignKey(Travel, on_delete=models.CASCADE) # 여행 제거시 해당 일차도 제거
    place = models.ForeignKey(Place, on_delete=models.CASCADE) # 장소 제거시 해당 일차도 제거
    date = models.DateField() # 여행 날짜

class PlaceImages(models.Model):
    # id: pk
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    image_url = models.URLField() # 이미지 url 정보를 저장합니다.

class Event(models.Model):
    category = models.CharField(max_length=100)
    gu_name = models.CharField(max_length=100)
    title = models.CharField(max_length=300)
    img_url = models.URLField()
    start_date = models.DateField()
    end_date = models.DateField()
    mapX = models.FloatField()
    mapY = models.FloatField()
    homepage_url = models.URLField()


