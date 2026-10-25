
from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "title",
            "message",
            "data",
            "is_read",
            "created_at",
            "read_at",
        ]
        read_only_fields = fields


class UnreadNotificationCountSerializer(serializers.Serializer):
    unread_count = serializers.IntegerField()


class MarkAllReadResponseSerializer(serializers.Serializer):
    updated_count = serializers.IntegerField()


class NotificationMessageSerializer(serializers.Serializer):
    detail = serializers.CharField()