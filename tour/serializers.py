from rest_framework import serializers
from .models import Travel
from .models import Event
from usr.serializers import UserSerializer

class TravelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Travel
        fields = '__all__' #포한하는 필드 지정, id는 장고에서 자동으로 생성!하니까 필드에 넣어두는 것이당!
        read_only_fields = ('user',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user.all(), many=True).data
        # data['user'] = instance.user.all().values_list('username', flat=True) # 사용자 username만 가져옵니다.
        return data

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
