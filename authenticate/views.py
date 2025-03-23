from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.response import Response
import requests
from rest_framework_simplejwt.views import TokenViewBase, TokenObtainPairView
from usr.serializers import UserAuthenticationSerializer

from usr.services import UserService

from config.settings import KAKAO_REST_API_KEY # 환경변수를 가져옵니다.

# Create your views here.


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
    # 토큰을 발급받기위한 요청 url 입니다.
    token_url = 'https://kauth.kakao.com/oauth/token'
    # 요청 body
    data = {
        'grant_type': 'authorization_code',
        'client_id': KAKAO_REST_API_KEY,
        'redirect_uri': redirect_uri,
        'code': code,
    }
    # 요청 헤더
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
    }
    # 토큰 발급을 요청합니다.
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code == 200:
        id_token = response.json().get('id_token', None)
        # 아이디 토큰이 존재하지 않는다면 -> 예외처리
        if id_token is None:
            return JsonResponse({"Error": "id 토큰이 존재하지 않습니다.", "ErrorResponse": response.json()})
        # TODO 유저 생성하여 회원가입 처리 or 로그인 처리
        user_service = UserService(id_token)
        user, is_new = user_service.get_or_register_user() # 로그인 혹은 회원가입을 처리합니다.
        # data 딕셔너리 객체를 생성하여 액세스, 리프레시 토큰만 골라서 추출
        data = dict()
        data['access_token'] = response.json().get('access_token', None)  # 액세스 토큰 추가
        data['token_type'] = response.json().get('token_type', None)  # token 타입 정보 추가
        data['refresh_token'] = response.json().get('refresh_token', None)  # 리프레시 토큰 정보 추가
        data['is_new'] = is_new # 신규 유저인지 알려주는 플래그 입니다.
        return JsonResponse(data, status=201) # post 요청을 보내줬기 때문에 201 create를 보내줍니다.
    return JsonResponse({"Error": response.text}, status=status.HTTP_400_BAD_REQUEST)

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
        # 토큰을 발급받기위한 요청 url 입니다.
        token_url = 'https://kauth.kakao.com/oauth/token'
        # 요청 헤더
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
        }
        data = {
            'grant_type': 'refresh_token',
            'client_id': KAKAO_REST_API_KEY,
            'refresh_token': refresh_token,
        }
        # 헤더와 정보를 조합하여 정보를 보냅니다.
        response = requests.post(token_url, data=data, headers=headers)
        # 올바른 정보가 넘어왔다면
        if response.status_code == 200:
            # data 딕셔너리 객체를 생성하여 액세스, 리프레시 토큰만 골라서 추출
            data = dict()
            data['access_token'] = response.json().get('access_token', None)  # 액세스 토큰 추가
            data['token_type'] = response.json().get('token_type', None)  # token 타입 정보 추가
            return Response(data, status=status.HTTP_201_CREATED)
        # 만일 토큰 정보가 잘못되었거나, refresh_token마저 만료 된경우, 혹은 카카오 측 오류인 경우
        return Response({"Error": response.text}, status=status.HTTP_400_BAD_REQUEST)

class IssueTokenView(TokenObtainPairView):
    serializer_class = UserAuthenticationSerializer

