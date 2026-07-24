from django.db import models

from apps.accounts.models import User
from apps.goals.models import SavingsGoal


class WithdrawalStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    REJECTED = "REJECTED", "Rejected"


class GoalWithdrawal(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="withdrawals"
    )

    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.CASCADE,
        related_name="withdrawals"
    )

    reference = models.CharField(
        max_length=100,
        unique=True,
        db_index=True
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=WithdrawalStatus.choices,
        default=WithdrawalStatus.PENDING
    )

    bank_name = models.CharField(
        max_length=100
    )

    account_name = models.CharField(
        max_length=150
    )

    account_number = models.CharField(
        max_length=20
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )

    requested_at = models.DateTimeField(
        auto_now_add=True
    )

    processed_at = models.DateTimeField(
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
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["goal"]),
            models.Index(fields=["status"]),
            models.Index(fields=["reference"]),
            models.Index(fields=["requested_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.reference} - {self.status}"