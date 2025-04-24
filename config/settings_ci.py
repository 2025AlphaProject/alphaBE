import settings

# 깃허브 ci 테스트를 위해 아래와 같이 DB를 설정합니다.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': settings.BASE_DIR / 'db.sqlite3',
    }
}