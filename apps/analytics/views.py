from django.db.models import Sum, Count, Q
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.goals.models import SavingsGoal, GoalStatus,GoalFunding
from decimal import Decimal
from django.db.models.functions import TruncMonth
from datetime import timedelta
from django.utils import timezone
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)


@extend_schema(
    tags=["Analytics"],
    summary="Goal summary",
    description="Returns a summary of the authenticated user's savings goals, including totals, statuses, and overall savings progress.",
    responses={
        200: OpenApiResponse(description="Goal summary retrieved successfully"),
    },
)
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

# GET /api/analytics/goals/?period=all

@extend_schema(
    tags=["Analytics"],
    summary="Monthly savings analytics",
    description="Returns monthly savings grouped by month for the selected time period.",
    parameters=[
        OpenApiParameter(
            name="period",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Time period: 1m, 3m, 6m, 1y, or all.",
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(description="Monthly savings retrieved successfully"),
        400: OpenApiResponse(description="Invalid period"),
    },
)
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


#Top savings
@extend_schema(
    tags=["Analytics"],
    summary="Top saving goals",
    description="Returns the user's top savings goals ordered by saved amount.",
    parameters=[
        OpenApiParameter(
            name="limit",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Maximum number of goals to return.",
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(description="Top saving goals retrieved successfully"),
        400: OpenApiResponse(description="Invalid limit"),
    },
)
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






#Recent Funding
@extend_schema(
    tags=["Analytics"],
    summary="Recent goal fundings",
    description="Returns the most recent funding transactions for the authenticated user's savings goals.",
    parameters=[
        OpenApiParameter(
            name="limit",
            type=int,
            location=OpenApiParameter.QUERY,
            description="Maximum number of funding records to return.",
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(description="Recent fundings retrieved successfully"),
        400: OpenApiResponse(description="Invalid limit"),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recent_goal_fundings(request):

    limit = request.query_params.get("limit", 5)

    try:
        limit = int(limit)
    except ValueError:
        return Response(
            {"detail": "Limit must be an integer."},
            status=400
        )

    fundings = (
        GoalFunding.objects
        .filter(goal__user=request.user)
        .select_related("goal")
        .order_by("-created_at")[:limit]
    )

    data = []

    for funding in fundings:
        data.append({
            "goal": funding.goal.name,
            "amount": funding.amount,
            "date": funding.created_at.date(),
        })

    return Response(data)



#Goal Funding
@extend_schema(
    tags=["Analytics"],
    summary="Goal funding details",
    description="Returns detailed funding statistics and funding history for a specific savings goal.",
    parameters=[
        OpenApiParameter(
            name="goal_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="Savings Goal ID",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Goal funding details retrieved successfully"),
        404: OpenApiResponse(description="Goal not found"),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def goal_funding_details(request, goal_id):

    goal = get_object_or_404(
        SavingsGoal,
        id=goal_id,
        user=request.user
    )

    fundings = (
        GoalFunding.objects
        .filter(goal=goal)
        .order_by("-created_at")
    )

    number_of_fundings = fundings.count()

    last_funding = fundings.first()

    progress_percentage = 0

    if goal.target_amount > 0:
        progress_percentage = round(
            (goal.saved_amount / goal.target_amount) * 100,
            2
        )

    data = {
        "goal": goal.name,
        "target_amount": goal.target_amount,
        "saved_amount": goal.saved_amount,
        "remaining_amount": goal.target_amount - goal.saved_amount,
        "progress_percentage": progress_percentage,
        "number_of_fundings": number_of_fundings,
        "last_funding": (
            last_funding.created_at
            if last_funding
            else None
        ),
        "fundings": [
            {
                "amount": funding.amount,
                "created_at": funding.created_at,
            }
            for funding in fundings
        ]
    }

    return Response(data)