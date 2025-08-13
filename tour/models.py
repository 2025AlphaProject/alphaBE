from django.db import models
from django.db.models import ForeignKey
from usr.models import User


# Create your models here.

class Travel(models.Model):
    # id: pk
    user = models.ManyToManyField(User) # 유저 제거시 해당 여행도 제거
    tour_name = models.CharField(max_length=255)  # 여행 이름 필드 추가
    tour_date = models.DateField() # 여행 날짜

    def __str__(self):
        return self.tour_name

class Place(models.Model):
    # id: pk
    name = models.CharField(max_length=100) # 장소 이름, 글자 수 제한
    mapX = models.FloatField() # 소수점 표현
    mapY = models.FloatField() # 소수점 표현
    road_address = models.TextField(blank=True, null=True) # 도로명 주소, 프론트로부터
    address = models.TextField(blank=True, null=True) # 지번 주소, 프론트 혹은 백의 비동기 작업으로부터
    cat1 = models.TextField(blank=True, null=True) # 소분류
    cat2 = models.TextField(blank=True, null=True) # 중분류
    cat3 = models.TextField(blank=True, null=True) # 대분류
    place_image = models.URLField(blank=True, null=True)
    areacode = models.CharField(max_length=255, blank=True, db_index=True)
    sigungucode = models.CharField(max_length=255, blank=True, db_index=True)
    contentid = models.CharField(max_length=255, blank=True, unique=True, db_index=True)
    contenttypeid = models.CharField(max_length=255, blank=True, db_index=True)
    zipcode = models.CharField(max_length=255, blank=True)
    lDongRegnCd = models.CharField(max_length=255, blank=True)
    lDongSignguCd = models.CharField(max_length=255, blank=True)
    lclsSystm1 = models.CharField(max_length=255, blank=True)
    lclsSystm2 = models.CharField(max_length=255, blank=True)
    lclsSystm3 = models.CharField(max_length=255, blank=True)
    tel = models.TextField(blank=True)

    def __str__(self):
        return self.name

class TravelDaysAndPlaces(models.Model):
    # id: pk
    travel = models.ForeignKey(Travel, on_delete=models.CASCADE) # 여행 제거시 해당 일차도 제거
    place = models.ForeignKey(Place, on_delete=models.CASCADE) # 장소 제거시 해당 일차도 제거

    def __str__(self):
        return self.travel.tour_name + " " + self.place.name + " " + str(self.travel.tour_date)

class PlaceImages(models.Model):
    # id: pk
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    image_url = models.URLField() # 이미지 url 정보를 저장합니다.

    def __str__(self):
        return self.place.name

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

    def __str__(self):
        return self.title

class SnapshotImages(models.Model):
    # id: pk
    tour = ForeignKey(Travel, on_delete=models.CASCADE)
    user = ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='', blank=True, null=True) # 이미지 필드를 추가합니다.

    def __str__(self):
        return f"{self.tour.tour_name} - {self.tour.tour_date} - snapshots"


class UserTourImage(models.Model):
    # id: pk
    tour = ForeignKey(Travel, on_delete=models.CASCADE)
    user = ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='', blank=True, null=True) # 이미지 필드를 추가합니다.

    def __str__(self):
        return f"{self.tour.tour_name} - {self.tour.tour_date} - userImage"

    class Meta:
        db_table = 'tour_images'