from django.db import models
from apps.accounts.models import User
from apps.wallet.models import Wallet


class GoalStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PAUSED = "PAUSED", "Paused"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"



class SavingsGoal(models.Model):
    user = models.ForeignKey( User,on_delete=models.CASCADE,related_name="goals")

    name = models.CharField(max_length=150)

    description = models.TextField(blank=True,null=True)

    target_amount = models.DecimalField(max_digits=12,decimal_places=2)

    saved_amount = models.DecimalField(max_digits=12,decimal_places=2,default=0)

    target_date = models.DateField(blank=True,null=True)

    status = models.CharField(max_length=20,choices=GoalStatus.choices,default=GoalStatus.ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["status"]),
            models.Index(fields=["target_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.name}"



class GoalFunding(models.Model):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="goal_fundings"
    )

    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.CASCADE,
        related_name="fundings"
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

    created_at = models.DateTimeField(
        auto_now_add=True
    )


    def __str__(self):
        return f"{self.user.email} - {self.name}"