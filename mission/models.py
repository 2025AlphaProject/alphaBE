from django.db import models

# Create your models here.
class Mission(models.Model): # 미션 모델을 생성합니다.
    # id: pk
    content = models.TextField() # 미션 내용 글자 수 제한 해제

    def __str__(self): # 미션 생성시 오브젝트가 아닌 미션 이름이 보이도록 수정
        return self.content