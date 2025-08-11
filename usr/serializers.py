from rest_framework import serializers

from .models import User, FCMToken


class UserSerializer(serializers.ModelSerializer):
    fcm_token = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['sub', 'username', 'profile_image_url', 'fcm_token']

class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = '__all__'
