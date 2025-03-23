from rest_framework import serializers
from rest_framework_simplejwt.tokens import Token

from .models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, AuthUser, TokenRefreshSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['sub', 'username', 'profile_image_url']

class UserAuthenticationSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self.fields['password'] # password 필드 제거

    def validate(self, attrs):
        sub = attrs.get("sub", None)

        try:
            user = User.objects.get(sub=sub)
        except User.DoesNotExist:
            # 유저를 찾을 수 없으면 회원가입을 진행합니다.
            raise serializers.ValidationError("사용자를 찾을 수 없습니다.")

        # 추가 검증 로직 (활성화 여부 등)
        if not user.is_active:
            raise serializers.ValidationError("비활성화된 계정입니다.")

        # 토큰 생성
        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    # @classmethod
    # def get_token(cls, user: AuthUser) -> Token:
    #     token = super().get_token(user)
    #     token['sub'] = user.sub
    #     token['username'] = user.username
    #     token['profile_image_url'] = user.profile_image_url
    #     token['gender'] = user.gender
    #     token['age_range'] = user.age_range
    #     return token