from rest_framework import serializers
from .models import Wallet, WalletTransaction


class WalletSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Wallet
        fields = [
            "id",
            "user",
            "available_balance",
            "total_funded",
            "total_transferred",
            "total_withdrawn",
            "total_refunded",
            "created_at",
            "updated_at",
        ]

        read_only_fields = fields


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            "id",
            "reference",
            "transaction_type",
            "amount",
            "balance_before",
            "balance_after",
            "status",
            "description",
            "created_at",
        ]

        read_only_fields = fields