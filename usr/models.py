from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    # username: Abstract User 필드 사용, 카카오 ID 토큰의 nickname으로 부터 추출하여 저장
    sub = models.BigIntegerField(primary_key=True)  # pk, 유저 고유 회원 번호를 의미하며, 카카오 ID 토큰으로 부터 추출합니다.
    # date_joined: 유저의 회원가입 날짜를 말하는 내장 필드로, 자동으로 정보가 add가 됩니다.
    # is_staff: 관리자 여부를 나타내는 것으로 가장 위의 권한인 superuser와 다른 개념입니다.
    # is_superuser: 가장 최상위 관리자를 나타냅니다.