from django.shortcuts import render
from rest_framework import viewsets
from .models import Mission
from .serializers import MissionSerializer


# Create your views here.
class MissionListView(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer