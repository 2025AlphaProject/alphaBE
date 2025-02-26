from .models import User
from config.settings import KAKAO_ADMIN_KEY
import requests
import jwt




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
        payload = jwt.decode(id_token, options={"verify_signature": False})
        self.sub = payload.get('sub', None) # 회원 번호 저장
        if self.sub is None:
            raise Exception("토큰 내 회원정보 일부가 존재하지 않습니다.")
        self.user = self.get_user() # 함수를 이용해서 유저를 가져옵니다.

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
        raise Exception()

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
