from django.db import models
from apps.accounts.models import User
from apps.wallet.models import Wallet
import uuid
from django.utils import timezone
from datetime import timedelta

class GoalStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    PAUSED = "PAUSED", "Paused"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"



class SavingsGoal(models.Model):
    owner = models.ForeignKey( User,on_delete=models.CASCADE,related_name="goals")

    name = models.CharField(max_length=150)

    description = models.TextField(blank=True,null=True)

    target_amount = models.DecimalField(max_digits=12,decimal_places=2,    null=True,
    blank=True)

    saved_amount = models.DecimalField(max_digits=12,decimal_places=2,default=0)

    target_date = models.DateField(blank=True,null=True)

    status = models.CharField(max_length=20,choices=GoalStatus.choices,default=GoalStatus.ACTIVE)


    is_shared = models.BooleanField(default=False)

    invite_code = models.CharField(
    max_length=50,
    unique=True,
    blank=True,
    null=True
)

    # allow_member_invites = models.BooleanField(default=False)


    require_owner_approval = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["status"]),
            models.Index(fields=["target_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["owner", "status"]),
        ]

    def __str__(self):
        return f"{self.owner.email} - {self.name}"



class GoalFunding(models.Model):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="goal_fundings"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="goal_fundings",
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
        return f"{self.user.email} - {self.goal.name}"





class GoalRole(models.TextChoices):
    OWNER = "OWNER", "Owner"
    CONTRIBUTOR = "CONTRIBUTOR", "Contributor"
    VIEWER = "VIEWER", "Viewer"




class GoalMemberStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    REJECTED = "REJECTED", "Rejected"


class GoalMember(models.Model):
    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.CASCADE,
        related_name="members"
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shared_goals"
    )

    role = models.CharField(
        max_length=20,
        choices=GoalRole.choices,
        default=GoalRole.CONTRIBUTOR
    )

    status = models.CharField(
        max_length=20,
        choices=GoalMemberStatus.choices,
        default=GoalMemberStatus.ACCEPTED
    )

    invited_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="goal_invites_sent"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("goal", "owner")



class InvitationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    ACCEPTED = "ACCEPTED", "Accepted"
    DECLINED = "DECLINED", "Declined"
    EXPIRED = "EXPIRED", "Expired"


class GoalInvitation(models.Model):
    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.CASCADE,
        related_name="invitations"
    )

    email = models.EmailField(db_index=True)

    invited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_goal_invitations"
    )

    token = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)



class GoalShareActivityType(models.TextChoices):
    GOAL_CREATED = "GOAL_CREATED", "Goal Created"
    MEMBER_INVITED = "MEMBER_INVITED", "Member Invited"
    MEMBER_JOINED = "MEMBER_JOINED", "Member Joined"
    MEMBER_DECLINED = "MEMBER_DECLINED", "Member Declined"
    MEMBER_REMOVED = "MEMBER_REMOVED", "Member Removed"
    MEMBER_LEFT = "MEMBER_LEFT", "Member Left"
    CONTRIBUTION = "CONTRIBUTION", "Contribution"
    GOAL_COMPLETED = "GOAL_COMPLETED", "Goal Completed"


class GoalShareActivity(models.Model):
    goal = models.ForeignKey(
        SavingsGoal,
        on_delete=models.CASCADE,
        related_name="activities"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="goal_share_activities"
    )

    activity_type = models.CharField(
        max_length=30,
        choices=GoalShareActivityType.choices
    )

    message = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]