from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from services.exception_handler import UnExpectedException, NoRequiredParameterException
from usr.models import User, FCMToken
from .serializers import UserSerializer, FCMTokenSerializer


class Who(ViewSet):
    permission_classes = [IsAuthenticated] # 로그인 사용자만 api 접근 허용

    def retrieve(self, request, pk=None):
        try:
            user = request.user  # request.user에서 정보 가져오기

            return Response({
                "sub": user.sub,
                "username": user.username,
                "profile_image_url": user.profile_image_url,
                "age_range": user.age_range,
                "gender": user.gender,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            raise UnExpectedException(error_message=str(e))

class UserListView(viewsets.ModelViewSet):
    """
    해당 클래스는 유저 리스트를 보여주는 뷰입니다.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user_name = self.request.GET.get('user_name', None)
        not_admin_user = User.objects.filter(is_superuser=False).filter(is_staff=False)
        if user_name is not None:
            return not_admin_user.filter(username__icontains=user_name)
        return not_admin_user

class UploadFcmTokenView(ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FCMTokenSerializer

    def create(self, request):
        """
            해당 메서드는 사용자의 fcm token을 저장합니다.
        """
        try:
            fcm = FCMToken.objects.get(fcm_token=request.data['fcm_token'])
            # 이미 요청된 fcm 토큰 존재하는 경우 등록 절차 생략
            return Response(status=status.HTTP_201_CREATED)
        except FCMToken.DoesNotExist:
            pass
        fcm_token = request.data.get('fcm_token', None)
        if not fcm_token:
            raise NoRequiredParameterException(
                error_message='fcm_token is required'
            )
        data = request.data.copy()
        data['user'] = request.user.sub
        serializer = FCMTokenSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        """
            fcm token은 매우 중요한 개인정보이기에 유저 정보 자체를 보내지 않습니다.
        """
        return Response(status=status.HTTP_201_CREATED)
