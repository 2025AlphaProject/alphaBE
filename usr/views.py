from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status

class Who(ViewSet):

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
