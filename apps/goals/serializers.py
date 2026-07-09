from rest_framework import serializers
from .models import SavingsGoal


class SavingsGoalSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            "id",
            "name",
            "description",
            "target_amount",
            "saved_amount",
            "target_date",
            "status",
            "progress",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "saved_amount",
            "status",
            "created_at",
            "updated_at",
        )

    def get_progress(self, obj):
        if obj.target_amount == 0:
            return 0

        return round((obj.saved_amount / obj.target_amount) * 100, 2)

    def validate_target_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Target amount must be greater than zero."
            )
        return value

from decimal import Decimal
from rest_framework import serializers


class GoalFundingSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def validate_amount(self, value):
        if value <= Decimal("0"):
            raise serializers.ValidationError(
                "Amount must be greater than zero."
            )

        return value