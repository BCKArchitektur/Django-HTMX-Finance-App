from rest_framework import serializers
from .models import ServiceProfile

class ServiceProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceProfile
        fields = ['id', 'name', 'excel_file', 'uploaded_at']
