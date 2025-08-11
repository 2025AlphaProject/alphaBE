from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    fcm_token = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['sub', 'username', 'profile_image_url', 'fcm_token']
