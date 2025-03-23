import requests
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from usr.models import User

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

        # 액세스 토큰 검증을 시도합니다.
        payload = self.validate_kakao_access_token(access_token)
        # 사용자 정보를 받아옵니다.
        try:
            sub = payload['id']
            user = User.objects.get(sub=sub)
            return user, access_token
        except User.DoesNotExist: # 사용자 정보가 없을 경우
            return None

    def validate_kakao_access_token(self, access_token):
        end_point = 'https://kapi.kakao.com/v1/user/access_token_info' # 유효성 검증 url
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(end_point, headers=headers)
        if response.status_code != 200:
            raise AuthenticationFailed('Invalid Kakao Access Token')
        return response.json()
