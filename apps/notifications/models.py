
import uuid

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        GENERAL = "GENERAL", "General"
        DEPOSIT_SUCCESS = "DEPOSIT_SUCCESS", "Deposit Successful"
        DEPOSIT_FAILED = "DEPOSIT_FAILED", "Deposit Failed"
        WITHDRAWAL_UPDATE = "WITHDRAWAL_UPDATE", "Withdrawal Update"
        WALLET_TRANSACTION = "WALLET_TRANSACTION", "Wallet Transaction"
        GOAL_FUNDING = "GOAL_FUNDING", "Goal Contribution"
        GOAL_COMPLETED = "GOAL_COMPLETED", "Goal Completed"
        GOAL_INVITATION = "GOAL_INVITATION", "Goal Invitation"
        GOAL_INVITATION_ACCEPTED = (
            "GOAL_INVITATION_ACCEPTED",
            "Goal Invitation Accepted",
        )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    type = models.CharField(
        max_length=40,
        choices=Type.choices,
        default=Type.GENERAL,
    )

    title = models.CharField(max_length=150)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)

    # A stable event key prevents duplicate notifications on retries.
    event_key = models.CharField(
        max_length=150,
        null=True,
        blank=True,
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "is_read", "-created_at"],
                name="notif_user_read_created_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event_key"],
                condition=models.Q(event_key__isnull=False),
                name="unique_user_notification_event",
            ),
        ]

    def __str__(self):
        return f"{self.title} - {self.user_id}"