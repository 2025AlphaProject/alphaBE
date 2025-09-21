from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.

class User(AbstractUser):
    # username: Abstract User 필드 사용, 카카오 ID 토큰의 nickname으로 부터 추출하여 저장
    sub = models.BigIntegerField(primary_key=True)  # pk, 유저 고유 회원 번호를 의미하며, 카카오 ID 토큰으로 부터 추출합니다.
    gender = models.CharField(max_length=20, null=True, blank=True) # male or female
    age_range = models.CharField(max_length=20, null=True, blank=True) # '1-9' 형식으로 들어옴
    profile_image_url = models.URLField() # 프로필 이미지 링크입니다.
    username = models.CharField(max_length=100)

    # 개인정보 취급 동의 시간
    privacy_policy_agree_time = models.DateTimeField(null=True, blank=True)
    # 개인정보 취급 동의 여부
    privacy_policy_agree = models.BooleanField(default=False)
    # 개인정보 취급 동의서 버전
    privacy_policy_version = models.CharField(max_length=255, null=True, blank=True)

    USERNAME_FIELD = 'sub'
    REQUIRED_FIELDS = ['username']

    def __str__(self): # 모델 자체에 이름을 부여합니다.
        return self.username

class FCMToken(models.Model):
    # id: pk
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fcm_token = models.CharField(max_length=500, null=True, blank=True) # 알림을 위한 클라이언트 측 fcm 토큰을 저장합니다.

    def __str__(self):
        return f'{self.user.username} - {self.id}'