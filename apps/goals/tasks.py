from celery import shared_task
from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from apps.goals.models import GoalInvitation, InvitationStatus,SavingsGoal



@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def check_goal_completion(self, goal_id):
    """
    Mark a savings goal as completed when its saved
    amount reaches or exceeds its target amount.
    """

    try:
        with transaction.atomic():
            goal = (
                SavingsGoal.objects
                .select_for_update()
                .filter(pk=goal_id)
                .first()
            )

            if goal is None:
                return {
                    "success": False,
                    "message": "Goal not found.",
                }

            # Do not overwrite other goal states.
            if goal.status != "ACTIVE":
                return {
                    "success": True,
                    "message": "Goal is not active.",
                    "status": goal.status,
                }

            if goal.target_amount is None:
                return {
                    "success": False,
                    "message": "Goal has no target amount.",
                }

            if goal.saved_amount >= goal.target_amount:
                goal.status = "COMPLETED"
                goal.save(update_fields=["status"])

                return {
                    "success": True,
                    "message": "Goal marked as completed.",
                    "goal_id": str(goal.pk),
                }

            return {
                "success": True,
                "message": "Goal target has not been reached.",
                "goal_id": str(goal.pk),
            }

    except Exception as exc:
        raise self.retry(exc=exc)






@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_goal_funding_notification(
    self,
    goal_id,
    contributor_email,
    amount,
    reference,
):
    goal = SavingsGoal.objects.filter(pk=goal_id).first()

    if goal is None:
        return {
            "success": False,
            "message": "Goal not found.",
        }

    # Support either the existing `user` field or
    # a renamed `owner` field.
    owner = (
        getattr(goal, "owner", None)
        or getattr(goal, "user", None)
    )

    owner_email = getattr(owner, "email", None)

    recipients = list(dict.fromkeys(
        email
        for email in (owner_email, contributor_email)
        if email
    ))

    if not recipients:
        return {
            "success": False,
            "message": "No notification recipients available.",
        }

    subject = f"New contribution to {goal.name}"

    message = (
        f"A contribution of {amount} was successfully made "
        f"to the savings goal '{goal.name}'.\n\n"
        f"Goal: {goal.name}\n"
        f"Contribution: {amount}\n"
        f"Reference: {reference}\n"
        f"Current saved amount: {goal.saved_amount}\n\n"
        "Log in to GoalSave to view your savings progress."
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )

        return {
            "success": True,
            "message": "Contribution notification sent.",
            "goal_id": str(goal.pk),
        }

    except Exception as exc:
        raise self.retry(exc=exc)





# apps/goals/tasks.py

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

from apps.goals.models import GoalInvitation, InvitationStatus


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_goal_invitation_email(self, invitation_id):
    try:
        invitation = GoalInvitation.objects.select_related(
            "goal",
            "invited_by",
        ).get(pk=invitation_id)

    except GoalInvitation.DoesNotExist:
        return {
            "success": False,
            "message": "Invitation not found.",
        }

    if invitation.status != InvitationStatus.PENDING:
        return {
            "success": False,
            "message": "Invitation is no longer pending.",
        }

    goal = invitation.goal
    inviter = invitation.invited_by

    # Set this to the base URL of your deployed backend.
    # For local testing, use http://127.0.0.1:8000
    backend_url = settings.GOALSAVE_BACKEND_URL.rstrip("/")

    accept_url = (
        f"{backend_url}/api/goals/invitations/"
        f"{invitation.token}/accept/"
    )

    decline_url = (
        f"{backend_url}/api/goals/invitations/"
        f"{invitation.token}/decline/"
    )

    subject = f"Invitation to join {goal.name} on GoalSave"

    message = (
        f"Hello,\n\n"
        f"{inviter.email} has invited you to join the shared savings "
        f"goal '{goal.name}' on GoalSave.\n\n"
        f"Goal: {goal.name}\n"
        f"Invited by: {inviter.email}\n\n"
        f"To accept this invitation, send an authenticated POST request to:\n"
        f"{accept_url}\n\n"
        f"To decline this invitation, send an authenticated POST request to:\n"
        f"{decline_url}\n\n"
        f"Important:\n"
        f"- Log in to GoalSave using {invitation.email}.\n"
        f"- These endpoints require authentication.\n"
        f"- The invitation may expire, so please respond promptly.\n"
        f"- Do not share these invitation links with anyone else.\n\n"
        f"If you weren't expecting this invitation, you can ignore this email.\n\n"
        f"Regards,\n"
        f"The GoalSave Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            fail_silently=False,
        )

        return {
            "success": True,
            "invitation_id": str(invitation.pk),
        }

    except Exception as exc:
        raise self.retry(exc=exc)