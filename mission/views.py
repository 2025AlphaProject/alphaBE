from django.shortcuts import render
from rest_framework import viewsets
from .models import Mission
from .serializers import MissionSerializer


# Create your views here.
class MissionListView(viewsets.ModelViewSet):
    queryset = Mission.objects.all()
    serializer_class = MissionSerializer


class MissionCheckCompleteView(viewsets.ModelViewSet):
    """
    Handles operations related to completing mission checks within the system.

    This class extends `viewsets.ModelViewSet` and is responsible for providing
    create, retrieve, update, and delete operations for mission check completion.
    It is tightly integrated with Django REST Framework and offers functionalities
    to manage mission check statuses effectively.

    Attributes:
        queryset: The default QuerySet used to retrieve objects. Typically, this is
            set to MissionCheckComplete.objects.all() or similar to include all
            mission completion records.
        serializer_class: The serializer class used to convert query objects into
            native Python data types and vice versa. This serializer handles
            validation and data transformation.
        permission_classes: List of permission classes that specify the access
            controls. This typically ensures only authorized users can perform
            operations on mission check data.

    """
    pass