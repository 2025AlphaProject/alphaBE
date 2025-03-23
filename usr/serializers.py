from rest_framework import serializers
from rest_framework_simplejwt.tokens import Token

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['sub', 'username', 'profile_image_url']
