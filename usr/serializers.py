from rest_framework import serializers

from .models import User, FCMToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['sub', 'username', 'profile_image_url']

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = '__all__'
