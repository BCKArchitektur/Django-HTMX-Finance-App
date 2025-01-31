from rest_framework import serializers
from .models import ServiceProfile

class ServiceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProfile
        fields = ['id', 'name', 'no_of_Honarzone', 'lp_breakdown']  # Include LP breakdown
