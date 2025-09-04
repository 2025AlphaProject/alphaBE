import logging

from rest_framework import serializers

from config.settings import APP_LOGGER, PUBLIC_DATA_PORTAL_API_KEY
from usr.serializers import UserSerializer
from .models import Travel, Place, Event, TravelDaysAndPlaces, PlaceImages, SnapshotImages, UserTourImage, RelationPlace
from services.tour_api_service import area_codes, TourAPIService
from .sigungu import SIGUNGU_DATA

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
        data['places'] = TravelDaysAndPlacesSerializer(TravelDaysAndPlaces.objects.filter(travel_id=instance.id), many=True).data
        return data

class TravelListSerializer(serializers.ModelSerializer):
    area_info = serializers.SerializerMethodField(allow_null=True)
    thumbnail = serializers.SerializerMethodField(allow_null=True)

    class Meta:
        model = Travel
        fields = '__all__'
        read_only_fields = ('user',)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('user')
        return data

    def get_area_info(self, obj):
        # 가장 첫번째 장소 정보만 가져옵니다. 여러 여행지를 여행하지 않는다 가정
        place = Place.objects.filter(traveldaysandplaces__travel_id=obj.id).first()
        area_name = None
        sigungu_name = None
        if place:
            area_name = area_codes.get(place.areacode)
        if area_name:
            areas = SIGUNGU_DATA.get(int(place.areacode))
            for sigungu in areas:
                if sigungu['code'] == place.sigungucode:
                    sigungu_name = sigungu['name']
                    break
        if area_name is None and sigungu_name is None: return None
        elif sigungu_name is None: return f'{area_name}'

        return f'{area_name} {sigungu_name}'

    def get_thumbnail(self, obj):
        # 가장 첫번째 사진만 가져옵니다.
        image = UserTourImage.objects.filter(tour_id=obj.id).first()
        if image is None: return None
        return image.image.url



class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class PlaceMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ('id', 'name', 'mapX', 'mapY', 'road_address', 'address', 'contenttypeid', 'place_image')

class PlaceSerializer(serializers.ModelSerializer):
    """
        해당 시리얼라이저는 장소 정보를 불러오거나 추가, 삭제를 진행할 때 사용합니다.
    """
    class Meta:
        model = Place
        fields = '__all__'

class TravelDaysAndPlacesSerializer(serializers.ModelSerializer):

    class Meta:
        model = TravelDaysAndPlaces
        fields = '__all__'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['tdp_id'] = data.pop('id')
        place_id = data.pop('place')
        data.pop('travel')
        data['place'] = PlaceMiniSerializer(Place.objects.get(id=place_id)).data
        return data

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

class UserTourImageSerializer(serializers.ModelSerializer):
    tour_date = serializers.CharField(source='tour.tour_date', read_only=True)
    class Meta:
        model = UserTourImage
        fields = '__all__'

    class TravelMiniSerializer(serializers.ModelSerializer):
        class Meta:
            model = Travel
            fields = ('id', 'tour_name')

    def to_representation(self, instance):
        # 사진 날짜 보여주기
        data = super().to_representation(instance)
        data['tour'] = UserTourImageSerializer.TravelMiniSerializer(instance=instance.tour).data
        data['user'] = UserSerializer(instance.user).data
        return data

class PoseRecommendSerializer(serializers.Serializer):
    place_id = serializers.CharField(max_length=255)
    poses = serializers.ListField(child=serializers.CharField(max_length=1000))
    images = serializers.ListField(child=serializers.URLField(max_length=1000))

class TodayTravelSerializer(serializers.Serializer):
    """
        당일 여행에 대한 정보를 위한 시리얼라이저 입니다.
        지역, 여행 인원수, 여행날짜, 사진 업로드 정보, 여행 장소 갯수, 관광타입정보
    """
    # 여행 이름
    tour_name = serializers.CharField(max_length=1000)
    # 여행날짜
    tour_date = serializers.DateField()
    # 여행 인원수
    people_cnt = serializers.IntegerField()
    # 사진 업로드 갯수
    image_cnt = serializers.IntegerField()
    # 여행 장소 갯수
    place_cnt = serializers.IntegerField()
    # 관광타입정보
    category_list = serializers.ListField(child=serializers.IntegerField())
    # 여행 지역 정보 (다수일 수 있으므로 리스트 형태로 제공)
    tour_area_info = serializers.ListField(child=serializers.CharField(max_length=1000))
    # 여행 아이디
    tour_id = serializers.IntegerField()


class MiniRelationPlaceSerializer(serializers.ModelSerializer):
    related_place_detail_info = PlaceMiniSerializer(source='related_place', read_only=True)
    class Meta:
        model = RelationPlace
        exclude = ('place_name', 'place_area_cd', 'place_area_name', 'place_sigungu_cd', 'place_sigungu_name')
