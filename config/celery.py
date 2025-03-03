import os

from celery import Celery

# 장고 환경 설정을 불러들입니다.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 장고는 앱 인스턴스가 굳이 여러개 구분할 필요가 없습니다.
app = Celery('config') # config 라는 프로젝트 이름으로 셀러리 앱을 생성합니다.

# 장고 세팅으로부터 셀러리 세팅을 불러오며, 셀러리 세팅 변수들은 항상 CELERY_ 라는 접두어를 붙입니다.
app.config_from_object('django.conf:settings', namespace='CELERY')

# 각 앱의 tasks.py에 있는 각 task들을 자동으로 감지합니다.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') # 로그를 발생시킵니다.