from rest_framework import serializers
from .models import LedgerEntry


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "transaction_reference",
            "transaction_type",
            "entry_type",
            "amount",
            "balance_before",
            "balance_after",
            "description",
            "created_at",
        ]