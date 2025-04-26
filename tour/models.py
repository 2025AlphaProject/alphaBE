from django.db import models
from usr.models import User
from mission.models import Mission

# Create your models here.

class Travel(models.Model):
    # id: pk
    user = models.ManyToManyField(User) # 유저 제거시 해당 여행도 제거
    tour_name = models.CharField(max_length=255)  # 여행 이름 필드 추가
    start_date = models.DateField() # 여행 시작 날짜
    end_date = models.DateField() # 여행 마감 날짜

class Place(models.Model):
    # id: pk
    name = models.CharField(max_length=100) # 장소 이름, 글자 수 제한
    mapX = models.FloatField() # 소수점 표현
    mapY = models.FloatField() # 소수점 표현
    road_address = models.TextField(blank=True, null=True) # 도로명 주소
    address = models.TextField(blank=True, null=True) # 지번 주소

class TravelDaysAndPlaces(models.Model):
    # id: pk
    travel = models.ForeignKey(Travel, on_delete=models.CASCADE) # 여행 제거시 해당 일차도 제거
    place = models.ForeignKey(Place, on_delete=models.CASCADE) # 장소 제거시 해당 일차도 제거
    date = models.DateField() # 여행 날짜
    mission = models.ForeignKey(Mission, on_delete=models.SET_NULL, blank=True, null=True) # 미션을 추가합니다. 미션 제거시 해당 일차 미션 NULL
    mission_image = models.ImageField(upload_to='', blank=True, null=True) # 이미지 필드를 추가합니다.

class PlaceImages(models.Model):
    # id: pk
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    image_url = models.URLField() # 이미지 url 정보를 저장합니다.

class Event(models.Model):
    # id: pk
    category = models.CharField(max_length=100) # 카테고리
    gu_name = models.CharField(max_length=100) # 구 이름을 말합니다.
    title = models.CharField(max_length=300) # 행사 제목
    img_url = models.URLField() # 행사 이미지 url 입니다.
    start_date = models.DateField() # 행사 시작 날짜
    end_date = models.DateField() # 행사 막날 날짜
    mapX = models.FloatField() # 행사 경도 정보
    mapY = models.FloatField() # 행사 위도 정보
    homepage_url = models.URLField() # 홈페이지 URL


