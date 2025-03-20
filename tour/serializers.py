from rest_framework import serializers
from .models import Travel
from .models import Event

class TravelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Travel
        fields = '__all__' #포한하는 필드 지정, id는 장고에서 자동으로 생성!하니까 필드에 넣어두는 것이당!
        read_only_fields = ('user',)

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'
