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

        # 카카오 토큰 정보를 보기 위한 URL 입니다.
        token_url = 'https://kapi.kakao.com/v1/user/access_token_info'
        headers = {'Authorization': 'Bearer ' + access_token}
        response = requests.get(token_url, headers=headers)
        if response.status_code == 400: # 카카오 플랫폼 서비스의 일시적 내부 장애 상태
            raise AuthenticationFailed('카카오 서비스 장애로 서비스를 이용하실 수 없습니다.')
        elif response.status_code == 401:
            raise AuthenticationFailed('Expired or Invalid Token')
        elif response.status_code == 200:
            sub = response.json().get('id')
            try:
                user = User.objects.get(sub=sub)
            except User.DoesNotExist:
                logger.warning('회원번호 ' + str(sub) + '인 회원이 존재하지 않습니다.')
                raise AuthenticationFailed('User not found')
            logger.info('회원번호 ' + str(sub) + '이 백엔드 api에 접근 중입니다.')
            return user, access_token
        logger.warning('알 수 없는 오류 발생')
        return None
