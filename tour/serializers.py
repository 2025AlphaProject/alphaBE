import logging

from rest_framework import serializers

from config.settings import APP_LOGGER
from usr.serializers import UserSerializer
from .models import Travel, Place, Event, TravelDaysAndPlaces, PlaceImages, SnapshotImages

logger = logging.getLogger(APP_LOGGER)

class TravelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Travel
        fields = '__all__' #포한하는 필드 지정, id는 장고에서 자동으로 생성!하니까 필드에 넣어두는 것이당!
        read_only_fields = ('user',)

    def to_representation(self, instance):
        logger.debug('Tour 시리얼라이저 to_representation 실행')
        data = super().to_representation(instance)
        data['user'] = UserSerializer(instance.user.all(), many=True).data
        # data['user'] = instance.user.all().values_list('username', flat=True) # 사용자 username만 가져옵니다.
        # instance는 DB 객체가 들어옴
        # 여행 id, tour_name, tour_date만 들어왔음
        data['places'] = PlaceSerializer(
            Place.objects.filter(traveldaysandplaces__travel=instance.id), many=True).data
        return data

class TravelListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Travel
        fields = '__all__'
        read_only_fields = ('user',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('user')
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

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            tdp = TravelDaysAndPlaces.objects.get(place_id=instance.id)
            data['tdp_id'] = tdp.id
        except TravelDaysAndPlaces.DoesNotExist:
            pass
        return data

class TravelDaysAndPlacesSerializer(serializers.ModelSerializer):
    # place = PlaceSerializer() # 장소 정보는 시리얼라이저를 통해 반환합니다.

    class Meta:
        model = TravelDaysAndPlaces
        fields = '__all__'

class PlaceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaceImages
        fields = '__all__'

class TourSnapshotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SnapshotImages
        fields = '__all__'

    def to_representation(self, instance):
        # 사진 날짜 보여주기
        data = super().to_representation(instance)
        data['tour_date'] = instance.tour.tour_date
        return data