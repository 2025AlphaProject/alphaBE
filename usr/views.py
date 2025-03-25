from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer

from usr.models import User


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
            return Response({"error": f"서버 오류: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserListView(viewsets.ModelViewSet):
    """
    해당 클래스는 유저 리스트를 보여주는 뷰입니다.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        user_name = self.request.GET.get('user_name', None)
        if user_name is not None:
            return User.objects.filter(username__icontains=user_name)
        return User.objects.all()
