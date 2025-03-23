import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from usr.models import User
import jwt # jwt 토큰 해석을 위해 필요합니다.
from config.settings import SECRET_KEY

import logging # 로그 작성을 위해서 사용됩니다.

logger = logging.getLogger('django')


class CustomAuthentication(BaseAuthentication):
    # authenticate 메소드 오버라이딩
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization') # Authorization 헤더 정보를 얻습니다.
        if not auth_header:
            logger.info('익명의 유저가 백엔드 api에 접근 중입니다.')
            return None # None으로 반환하는 경우 Django의 AnonymousUser로 인식됩니다.

        try:
            prefix, access_token = auth_header.split(' ')
        except ValueError:
            raise AuthenticationFailed('Invalid Bearer Prefix')
        if prefix != 'Bearer':
            raise AuthenticationFailed('Invalid Bearer Prefix')

        # jwt 토큰을 디코드합니다.
        payload = None
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=['HS256']) # 장고 시크릿 키로 해독을 시도합니다.
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Expired Token')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid Token')
        # 사용자 정보를 받아옵니다.
        try:
            sub = payload['sub']
            user = User.objects.get(sub=sub)
            return user, access_token
        except User.DoesNotExist: # 사용자 정보가 없을 경우
            raise AuthenticationFailed('User not found')
