from rest_framework import serializers
from .models import *


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('__all__')

        read_only_fields = ['id', 'created_at']
