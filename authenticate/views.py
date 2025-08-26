import logging

from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from config.settings import KAKAO_REAL_NATIVE_API_KEY, KAKAO_REST_API_KEY, APP_LOGGER  # 환경변수를 가져옵니다.
from services.exception_handler import *
from services.kakao_error_handler import KakaoRequestError
from services.kakao_token_service import KakaoTokenService
from usr.services import UserService, TestUserCreationService

logger = logging.getLogger(APP_LOGGER)

# Create your views here.

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def kakao_callback(request):
    """
    해당 메소드는 카카오 인가코드를 이용하여 액세스 토큰을 발급하여 로그인 처리를 진행합니다.
    """

    # code는 카카오에서 제공받은 인가코드를 말합니다.
    code = request.GET.get('code', None)  # url 쿼리 파라미터로부터 code를 가져옵니다.
    redirect_uri = request.GET.get('redirect_uri', None)  # url 퀴리 파라미터로 클라이언트 측 redirect_uri를 가져옵니다.
    # 인가 코드가 추출되지 않는 경우 예외 처리
    if code is None:
        return JsonResponse({"Error": "인가 코드 추출 실패"}, status=status.HTTP_400_BAD_REQUEST)
    # 토큰을 발급받기위한 클래스 선언
    token_service = KakaoTokenService(KAKAO_REST_API_KEY)
    tokens = token_service.get_tokens(code, redirect_uri)
    user_service = UserService(tokens.id_token)
    user, is_new = user_service.get_or_register_user()  # 로그인 혹은 회원가입을 처리합니다.
    data = dict()
    data['access_token'] = tokens.access_token  # 액세스 토큰 추가
    data['token_type'] = tokens.token_type  # token 타입 정보 추가
    data['refresh_token'] = tokens.refresh_token  # 리프레시 토큰 정보 추가
    data['id_token'] = tokens.id_token
    data['is_new'] = is_new # 신규 유저인지 알려주는 플래그 입니다.
    return JsonResponse(data, status=201) # post 요청을 보내줬기 때문에 201 create를 보내줍니다.

class KakaoRefreshTokens(viewsets.ViewSet):
    """
    해당 클래스는 카카오 세션이 만료되었을 때 refresh를 해주기 위한 api view 입니다.
    """
    def create(self, request):
        # refresh_token 파싱
        refresh_token = request.data.get('refresh_token', None)
        # refresh_token이 body에 존재하지 않는다면
        if refresh_token is None:
            return Response({"Error": "Refresh token is missing"}, status=400)
        # 리프레시 토큰이 있는경우
        token_service = KakaoTokenService(KAKAO_REAL_NATIVE_API_KEY)
        try:
            tokens = token_service.get_new_tokens(refresh_token) # 카카오 토큰을 재발급 받습니다.
            data = dict()
            data['access_token'] = tokens.access_token  # 액세스 토큰 추가
            data['token_type'] = tokens.token_type  # token 타입 정보 추가
            data['refresh_token'] = tokens.refresh_token # 리프레시 추가 None 가능
            return Response(data, status=status.HTTP_201_CREATED)
        except KakaoRequestError as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginRegisterView(viewsets.ViewSet):
    """
    해당 뷰는 로그인/회원가입 뷰 역할을 하며 실제 DB속 회원이 존재하면 로그인 처리를,
    그렇지 않다면 회원가입을 처리합니다.
    Header
      Authorization: Bearer <access_token>

    """
    # permission_classes = [IsAuthenticated] # 카카오 로그인이 된 사용자, 유효한 토큰을 가진 사용자만 서비스 로그인, 회원가입을 처리합니다.

    def create(self, request):
        id_token = request.data.get('id_token', None)

        if id_token is None: # id token 정보가 없는 경우
            return Response({"Error": "id_token 정보가 존재하지 않습니다."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if id_token == 'tester': # 테스터 로그인이라면
                user_service = TestUserCreationService()
                user, is_new = user_service.get_or_create_test_user()
            else:
                user_service = UserService(id_token)
                user, is_new = user_service.get_or_register_user() # 로그인, 회원가입 처리
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        tokens = get_tokens_for_user(user)
        accessToken = tokens['access']
        refreshToken = tokens['refresh']

        return Response({
            "message": "login or register success",
            "is_new": is_new,
            "user": {
                "username": user.username,
                "sub": user.sub,
                "profile_image_url": user.profile_image_url,
                "age_range": user.age_range,
                "gender": user.gender,
            },
            "tokens": {
                "access_token": accessToken,
                "refresh_token": refreshToken,
            }
        }, status=status.HTTP_201_CREATED)

class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        refresh_token = data.pop('refresh_token', None)
        if refresh_token is None:
            raise NoRequiredParameterException(
                'NO_PARAMETER',
                'refresh_token 키 값이 존재하지 않습니다.'
            )
        data['refresh'] = refresh_token
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            raise ExceptionHandler(
                'TOKEN_VALIDATION_ERROR',
                e
            )

        return Response({
            'access_token': serializer.validated_data['access'],
            'token_type': 'Bearer',
            'refresh_token': serializer.validated_data['refresh'],
        }, status=status.HTTP_200_OK)