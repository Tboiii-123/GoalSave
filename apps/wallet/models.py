from django.db import models
from apps.accounts.models import User


class TransactionType(models.TextChoices):
    DEPOSIT = "DEPOSIT", "Deposit"
    TRANSFER = "TRANSFER", "Transfer"
    WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
    REFUND = "REFUND", "Refund"


class TransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class Wallet(models.Model):
    user = models.OneToOneField(    User, on_delete=models.CASCADE,related_name="wallet")

    available_balance = models.DecimalField(max_digits=12,decimal_places=2,default=0)

    total_funded = models.DecimalField(max_digits=12,decimal_places=2,default=0)

    total_transferred = models.DecimalField(max_digits=12,decimal_places=2, default=0)

    total_withdrawn = models.DecimalField(max_digits=12,decimal_places=2,default=0)

    total_refunded = models.DecimalField(max_digits=12,decimal_places=2,default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} Wallet"


class WalletTransaction(models.Model):
    wallet = models.ForeignKey(Wallet,on_delete=models.CASCADE,related_name="transactions")

    reference = models.CharField(max_length=100,unique=True)

    transaction_type = models.CharField(max_length=20,choices=TransactionType.choices)

    amount = models.DecimalField(max_digits=12,decimal_places=2)

    balance_before = models.DecimalField(max_digits=12,decimal_places=2)

    balance_after = models.DecimalField(max_digits=12,decimal_places=2)

    status = models.CharField(max_length=20,choices=TransactionStatus.choices,default=TransactionStatus.PENDING)

    description = models.TextField(blank=True,null=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["wallet", "status"]),
        ]

    def __str__(self):
        return f"{self.reference} - {self.transaction_type}"