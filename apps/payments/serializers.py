from rest_framework import serializers

from .models import DepositTransaction

class DepositInitiateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value



class DepositTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositTransaction
        fields = [
            "reference",
            "amount",
            "status",
            "gateway",
            "paid_at",
            "created_at",
        ]