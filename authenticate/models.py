from django.db import models

# Create your models here.

class OIDC(models.Model):
    """
    해당 모델은 카카오 OIDC 목록을 캐싱하기 위해서 사용하는 모델입니다.
    """
    kid = models.TextField() # 공개키 ID
    n = models.TextField() # 공개키 모듈
    e = models.CharField(max_length=100) # 공개키 지수
    last_updated = models.DateTimeField(auto_now=True) # 업데이트 마지막 날짜