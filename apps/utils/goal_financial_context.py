from apps.goals.models import SavingsGoal, GoalFunding
from apps.wallet.models import Wallet


def build_goal_ai_context(*, user, goal: SavingsGoal) -> dict:

    wallet = Wallet.objects.filter(user=user).first()

    fundings = (
        GoalFunding.objects
        .filter(
            goal=goal,
            user=user,
        )
        .order_by("-created_at")[:10]
    )

    calculations = calculate_goal_statistics(goal)

    return {
        "goal": {
            "id": goal.id,
            "name": goal.name,
            "description": goal.description,
            "target_amount": (
                str(goal.target_amount)
                if goal.target_amount is not None
                else None
            ),
            "saved_amount": str(goal.saved_amount),
            "target_date": (
                goal.target_date.isoformat()
                if goal.target_date
                else None
            ),
            "status": goal.status,
        },

        "wallet": {
            "available_balance": (
                str(wallet.available_balance)
                if wallet
                else "0.00"
            ),
        },

        "recent_goal_fundings": [
            {
                "amount": str(funding.amount),
                "created_at": funding.created_at.isoformat(),
                "reference": funding.reference,
            }
            for funding in fundings
        ],

        "calculations": calculations,
    }

from decimal import Decimal, ROUND_UP
from django.utils import timezone


def calculate_goal_statistics(goal) -> dict:
    """
    Calculate financial statistics for a single savings goal.

    All financial calculations are performed by the backend,
    not by the LLM.
    """

    target_amount = goal.target_amount
    saved_amount = goal.saved_amount or Decimal("0.00")

    if target_amount is not None:
        remaining_amount = max(
            target_amount - saved_amount,
            Decimal("0.00"),
        )

        progress_percentage = (
            (saved_amount / target_amount) * Decimal("100")
            if target_amount > 0
            else Decimal("0.00")
        )
    else:
        remaining_amount = None
        progress_percentage = None

    days_remaining = None
    weeks_remaining = None
    required_weekly_saving = None
    required_monthly_saving = None

    if goal.target_date:
        today = timezone.localdate()
        days_remaining = max(
            (goal.target_date - today).days,
            0,
        )

        if days_remaining > 0 and remaining_amount is not None:
            weeks_remaining = Decimal(days_remaining) / Decimal("7")

            required_weekly_saving = (
                remaining_amount / weeks_remaining
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_UP,
            )

            required_monthly_saving = (
                remaining_amount
                / (Decimal(days_remaining) / Decimal("30.44"))
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_UP,
            )

    return {
        "remaining_amount": (
            str(remaining_amount)
            if remaining_amount is not None
            else None
        ),
        "progress_percentage": (
            str(
                progress_percentage.quantize(
                    Decimal("0.01")
                )
            )
            if progress_percentage is not None
            else None
        ),
        "days_remaining": days_remaining,
        "weeks_remaining": (
            str(
                weeks_remaining.quantize(
                    Decimal("0.01")
                )
            )
            if weeks_remaining is not None
            else None
        ),
        "required_weekly_saving": (
            str(required_weekly_saving)
            if required_weekly_saving is not None
            else None
        ),
        "required_monthly_saving": (
            str(required_monthly_saving)
            if required_monthly_saving is not None
            else None
        ),
    }