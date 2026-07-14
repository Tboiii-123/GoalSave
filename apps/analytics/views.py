from django.db.models import Sum, Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.goals.models import SavingsGoal, GoalStatus,GoalFunding
from decimal import Decimal
from django.db.models.functions import TruncMonth
from datetime import timedelta
from django.utils import timezone

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def goal_summary(request):

    goals = SavingsGoal.objects.filter(user=request.user)

    summary = goals.aggregate( total_goals=Count("id"),

        active_goals=Count(
            "id",
            filter=Q(status=GoalStatus.ACTIVE)
        ),

        completed_goals=Count(
            "id",
            filter=Q(status=GoalStatus.COMPLETED)
        ),

        paused_goals=Count(
            "id",
            filter=Q(status=GoalStatus.PAUSED)
        ),

        cancelled_goals=Count(
            "id",
            filter=Q(status=GoalStatus.CANCELLED)
        ),

        total_target_amount=Sum("target_amount"),

        total_saved_amount=Sum("saved_amount"),
    )

    total_target = summary["total_target_amount"] or Decimal("0.00")
    total_saved = summary["total_saved_amount"] or Decimal("0.00")

    if total_target > 0:
        overall_progress = round(
            (total_saved / total_target) * 100,
            2
        )
    else:
        overall_progress = Decimal("0.00")

    return Response({
        "total_goals": summary["total_goals"],
        "active_goals": summary["active_goals"],
        "completed_goals": summary["completed_goals"],
        "paused_goals": summary["paused_goals"],
        "cancelled_goals": summary["cancelled_goals"],
        "total_target_amount": total_target,
        "total_saved_amount": total_saved,
        "overall_progress_percentage": overall_progress,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def monthly_savings(request):

    monthly_data = GoalFunding.objects.filter(goal__user=request.user).annotate(month=TruncMonth("created_at")).values("month").annotate(amount=Sum("amount")).order_by("month")
    

    data = []

    for item in monthly_data:
        data.append({
            "month": item["month"].strftime("%Y-%m"),
            "amount": item["amount"],
        })

    return Response(data)
# GET /api/analytics/goals/?period=all


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def monthly_savings(request):

    period = request.query_params.get("period", "3m")

    queryset = GoalFunding.objects.filter(
        goal__user=request.user
    )

    today = timezone.now()

    if period == "1m":
        start_date = today - timedelta(days=30)
        queryset = queryset.filter(created_at__gte=start_date)

    elif period == "3m":
        start_date = today - timedelta(days=90)
        queryset = queryset.filter(created_at__gte=start_date)

    elif period == "6m":
        start_date = today - timedelta(days=180)
        queryset = queryset.filter(created_at__gte=start_date)

    elif period == "1y":
        start_date = today - timedelta(days=365)
        queryset = queryset.filter(created_at__gte=start_date)

    elif period == "all":
        pass

    else:
        return Response(
            {
                "detail": "Invalid period. Use one of: 1m, 3m, 6m, 1y, all."
            },
            status=400
        )

    monthly_data = (
        queryset
        .annotate(
            month=TruncMonth("created_at")
        )
        .values("month")
        .annotate(
            amount=Sum("amount")
        )
        .order_by("month")
    )

    data = []

    for item in monthly_data:
        data.append({
            "month": item["month"].strftime("%Y-%m"),
            "amount": item["amount"],
        })

    return Response({
        "period": period,
        "data": data
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def top_saving_goals(request):

    limit = request.query_params.get("limit", 5)

    try:
        limit = int(limit)
    except ValueError:
        return Response(
            {"detail": "Limit must be an integer."},
            status=400
        )

    goals = (
        SavingsGoal.objects
        .filter(user=request.user)
        .order_by("-saved_amount")[:limit]
    )

    data = []

    for goal in goals:
        progress = 0

        if goal.target_amount > 0:
            progress = round(
                (goal.saved_amount / goal.target_amount) * 100,
                2
            )

        data.append({
            "id": goal.id,
            "goal": goal.name,
            "saved_amount": goal.saved_amount,
            "target_amount": goal.target_amount,
            "progress_percentage": progress,
            "status": goal.status,
        })

    return Response(data)