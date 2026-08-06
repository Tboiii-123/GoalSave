from rest_framework import serializers

from .models import GoalWithdrawal


class GoalWithdrawalSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoalWithdrawal
        fields = [
            "id",
            "goal",
            "amount",
            "bank_name",
            "account_name",
            "account_number",
            "status",
            "reference",
            "requested_at",
        ]

        read_only_fields = [
            "id",
            "status",
            "reference",
            "requested_at",
        ]