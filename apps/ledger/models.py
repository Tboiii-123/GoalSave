from django.db import models

from apps.wallet.models import Wallet


class LedgerEntryType(models.TextChoices):
    DEBIT = "DEBIT", "Debit"
    CREDIT = "CREDIT", "Credit"


class LedgerTransactionType(models.TextChoices):
    DEPOSIT = "DEPOSIT", "Deposit"
    TRANSFER = "TRANSFER", "Transfer"
    WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
    REFUND = "REFUND", "Refund"


class LedgerEntry(models.Model):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="ledger_entries"
    )

    transaction_reference = models.CharField(
        max_length=100,
        db_index=True
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=LedgerTransactionType.choices
    )

    entry_type = models.CharField(
        max_length=10,
        choices=LedgerEntryType.choices
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    balance_before = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    balance_after = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "created_at"]),
            models.Index(fields=["transaction_reference"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["entry_type"]),
        ]

    def __str__(self):
        return f"{self.transaction_reference} - {self.entry_type}"