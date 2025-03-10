from django.db import models

# Create your models here.
class Mission(models.Model): # 미션 모델을 생성합니다.
    # id: pk
    content = models.TextField() # 미션 내용 글자 수 제한 해제