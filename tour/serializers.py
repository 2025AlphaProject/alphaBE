from rest_framework import serializers
from .models import Travel

class TravelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Travel
        fields = ['id','tour_name', 'start_date', 'end_date'] #포한하는 필드 지정, id는 장고에서 자동으로 생성!하니까 필드에 넣어두는 것이당!

