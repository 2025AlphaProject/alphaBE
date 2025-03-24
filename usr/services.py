from django.core.exceptions import ValidationError

from .models import User
from config.settings import KAKAO_ADMIN_KEY
import requests
import jwt
import base64
import json
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from authenticate.models import OIDC




class UserService:
    """
    해당 클래스는 유저를 찾고, 없으면 회원가입 즉, DB에 등록하는 작업을 하는 클래스로 인스턴스 변수 user는 User 모델 클래스를, sub는 카카오
    고유 회원번호로 long 형식입니다.
    """
    user = None
    sub = None # sub는 long 방식의 정수형을 받습니다.

    def __init__(self, id_token):
        """
        해당 함수는 유저 서비스 객체가 생성될 때 자동으로 실행되는 함수입니다.
        :param id_token: 회원 정보가 들어있는 아이디 토큰입니다.
        """
        # payload = jwt.decode(id_token, options={"verify_signature": False})
        payload = self.__validate_id_token(id_token)
        self.sub = payload.get('sub', None) # 회원 번호 저장
        if self.sub is None:
            raise Exception("토큰 내 회원정보 일부가 존재하지 않습니다.")
        self.user = self.get_user() # 함수를 이용해서 유저를 가져옵니다.

    def __jwt_to_pem(self, n, e):
        """
        해당 함수는 Base64 URL safe 인코딩된 값이므로 이를 디코딩하여 pem 형식으로 변환
        """
        n = int.from_bytes(base64.urlsafe_b64decode(n + '=='), 'big')
        e = int.from_bytes(base64.urlsafe_b64decode(e + '=='), 'big')
        public_key = rsa.RSAPublicNumbers(e, n).public_key(default_backend())
        return public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

    def __validate_id_token(self, id_token):
        """
        해당 함수는 id_token을 검증하기 위한 함수입니다.
        """
        # id 토큰에서 헤더 정보만 분리
        header = id_token.split('.')[0]
        # 헤더에서 kid 부분만 분리
        header = json.loads(base64.b64decode(header).decode('utf-8'))
        kid = header['kid']
        # OIDC api 통해서 공개키 목록 조회
        # 일치하는 공개키를 찾아서 시크릿 키로 지정
        key = self.__get_public_pem_key(kid)
        # jwt 토큰 유효성 검증
        payload = jwt.decode(id_token, key, algorithms=['RS256'],
                             options={
                                 "verify_aud": False,
                                 "verify_iat": False, # 서버 시간과 미세하게 일치하지 않아 발생하는 오류를 무시합니다.
                             })
        return payload

    def __validate_header(self):
        """
        해당 함수는 페이로드의 키별 값을 검증합니다.
        iss: https://kauth.kakao.com
        aud: 서비스 앱 키와 일치해야함
        """
        pass

    def __download_oidc(self):
        """
        oidc 코드 DB 저장
        """
        # TODO oidc 다운로드 로거 추가
        end_point = 'https://kauth.kakao.com/.well-known/jwks.json'
        response = requests.get(end_point)
        result = response.json()['keys']
        # OIDC 테이블 초기화
        OIDC.objects.all().delete()

        for each in result:
            OIDC.objects.create(
                kid=each['kid'],
                n=each['n'],
                e=each['e']
            )


    def __get_public_pem_key(self, kid):
        # db에서 kid에 해당하는 아이디를 가져옵니다.
        try:
            OIDC.objects.get(kid=kid)
        except OIDC.DoesNotExist: # 해당하는 키가 없을 때 키 변경을 감지하고 다운로드 진행
            self.__download_oidc()
        oidc = None
        try:
            oidc = OIDC.objects.get(kid=kid)
        except OIDC.DoesNotExist: # 오류 발생
            raise ValidationError("카카오 JWT 헤더 손상 의심")
        return self.__jwt_to_pem(oidc.n, oidc.e)




    def get_or_register_user(self):
        """
        :return: user(User object), isNew(bool)
        """
        if self.user is None: # 유저가 존재하지 않는다면 가입을 진행
            return self.register_user(), True
        return self.user, False

    def get_user(self):
        """
        :param sub: 카카오 고유 회원번호를 의미합니다.
        """
        user = None
        try:
            user = User.objects.get(sub=self.sub) # 유저를 가져오는 시도를 합니다.
            return user
        except User.DoesNotExist:
            # 유저가 존재하지 않는다면 None으로 판단하여 반환
            return None

    def register_user(self):
        """
        해당 함수는 신규 유저를 실제로 DB에 등록하는 역할을 합니다.
        """
        # 회원가입 시작
        # 카카오 개인 유저 정보를 갖고 오기 위한 url
        kakao_user_info_url = f'https://kapi.kakao.com/v2/user/me?target_id_type=user_id&target_id={self.sub}'

        header = {
            'Authorization': f'KakaoAK {KAKAO_ADMIN_KEY}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        response = requests.get(kakao_user_info_url, headers=header)  # 요청을 받아옵니다.
        if response.status_code == 200:  # 정상적으로 데이터가 왔다면
            return self.__upload_user(response.json()) # 실제 데이터 업로드를 진행합니다.
        raise Exception("카카오 회원정보를 불러오는 과정에서 오류가 발생했습니다.")

    def __upload_user(self, raw_data):
        """
        해당 함수는 실제로 DB에 유저를 등록하는 로직이며 private 함수입니다.
        :params raw_data: 카카오에서 날라오는 json 정보 그대로를 말합니다.
        """
        data_dict = dict() # 실제 데이터가 저장될 정보입니다.
        raw_data = raw_data['kakao_account'] # 카카오 계정 정보로 대체 저장
        profile = raw_data['profile'] # 추가 파싱 데이터
        # sub 저장
        data_dict['sub'] = self.sub
        # 닉네임 저장
        data_dict['username'] = profile['nickname']
        # 프로필 이미지 url 저장
        data_dict['profile_image_url'] = profile['profile_image_url']
        user_dict_keys = ['age_range', # 연령대
                          'gender'] # 성별
        for each in user_dict_keys:
            data_dict[each] = raw_data[each]

        # 실제 유저 업로드
        try:
            user = User.objects.create(**data_dict)
        except Exception as e:
            raise Exception(e)
        return user
