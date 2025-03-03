from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import jwt
from .services import UserService

class Who(APIView):

    def get(self, request):
        id_token = request.headers.get("Authorization") #idtoken 가져오기

        if not id_token:  #id token 없을 때 예외 처리
            return Response({"error": "id_token이 제공되지 않았습니다."}, status=status.HTTP_401_UNAUTHORIZED)

        try: #유저 정보 가져오기
            user_service = UserService(id_token)
            user = user_service.get_or_register_user()

            #유저 정보를 JSON 형태로?
            return Response({
                "sub": user.sub,
                "username": user.username,
                "profile_image_url": user.profile_image_url,
                "age_range": user.age_range,
                "gender": user.gender,
            }, status=status.HTTP_200_OK)

        #예외 처리
        except (jwt.ExpiredSignatureError, jwt.DecodeError):
            return Response({"error": "토큰이 만료되었거나 유효하지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"error": f"서버 오류: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
