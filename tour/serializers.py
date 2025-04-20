from rest_framework import serializers
from .models import Travel, Place, Event
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

class PlaceSerializer(serializers.ModelSerializer):
    """
        해당 시리얼라이저는 장소 정보를 불러오거나 추가, 삭제를 진행할 때 사용합니다.
    """
    class Meta:
        model = Place
        fields = '__all__'
