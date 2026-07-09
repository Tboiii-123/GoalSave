from django.db import models
from apps.accounts.models import User
from apps.wallet.models import Wallet


class PaymentGateway(models.TextChoices):
    PAYSTACK = "PAYSTACK", "Paystack"
    FLUTTERWAVE = "FLUTTERWAVE", "Flutterwave"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"


class DepositTransaction(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="deposits"
    )

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="deposits"
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    gateway_reference = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True
    )

    gateway = models.CharField(
        max_length=20,
        choices=PaymentGateway.choices
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )

    gateway_response = models.JSONField(
        default=dict,
        blank=True
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True
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
            models.Index(fields=["reference"]),
            models.Index(fields=["gateway_reference"]),
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.reference} - {self.amount}"