from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    # username: Abstract User 필드 사용, 카카오 ID 토큰의 nickname으로 부터 추출하여 저장
    sub = models.BigIntegerField(primary_key=True)  # pk, 유저 고유 회원 번호를 의미하며, 카카오 ID 토큰으로 부터 추출합니다.
    gender = models.CharField() # male or female
    age_range = models.CharField() # '1-9' 형식으로 들어옴
    profile_image_url = models.URLField() # 프로필 이미지 링크입니다.

    def __str__(self): # 모델 자체에 이름을 부여합니다.
        return self.username