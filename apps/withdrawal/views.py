from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.goals.models import SavingsGoal, GoalStatus
from apps.ledger.models import LedgerEntry,LedgerTransactionType, LedgerEntryType
from apps.wallet.models import  Wallet
from .models import GoalWithdrawal, WithdrawalStatus
from .serializers import GoalWithdrawalSerializer
from .utils import generate_withdrawal_reference

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)



@extend_schema(
    tags=["Withdrawals"],
    summary="Request a withdrawal",
    description=(
        "Creates a withdrawal request for a matured or completed savings goal. "
        "The request is submitted for admin approval before funds are released."
    ),
    request=GoalWithdrawalSerializer,
    responses={
        201: GoalWithdrawalSerializer,
        400: OpenApiResponse(
            description=(
                "Validation error, goal not matured, insufficient balance, "
                "or an existing pending withdrawal."
            )
        ),
        403: OpenApiResponse(description="You do not own this goal"),
    },
    examples=[
        OpenApiExample(
            "Withdrawal Request",
            request_only=True,
            value={
                "goal": "b4d66dd4-4c75-4dd8-a4fa-8c90b62f4d2e",
                "amount": 50000,
                "bank_name": "Access Bank",
                "account_name": "John Doe",
                "account_number": "0123456789",
            },
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_withdrawal(request):

    serializer = GoalWithdrawalSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    goal = serializer.validated_data["goal"]
    amount = serializer.validated_data["amount"]

    if goal.user != request.user:
        return Response(
            {"detail": "You do not own this goal."},
            status=status.HTTP_403_FORBIDDEN
        )

    if goal.status == GoalStatus.CANCELLED:
        return Response(
            {"detail": "This goal has been cancelled."},
            status=status.HTTP_400_BAD_REQUEST
        )

    today = timezone.now().date()

    matured = (
        goal.target_date is not None and
        goal.target_date <= today
    )

    completed = goal.status == GoalStatus.COMPLETED

    if not (matured or completed):
        return Response(
            {"detail": "Goal has not matured yet."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if amount <= 0:
        return Response(
            {"detail": "Amount must be greater than zero."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if amount > goal.saved_amount:
        return Response(
            {"detail": "Insufficient goal balance."},
            status=status.HTTP_400_BAD_REQUEST
        )

    with transaction.atomic():

        goal = SavingsGoal.objects.select_for_update().get(
            id=goal.id
        )

        if GoalWithdrawal.objects.filter(
            goal=goal,
            status=WithdrawalStatus.PENDING
        ).exists():
            return Response(
                {
                    "detail": "There is already a pending withdrawal for this goal."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        withdrawal = GoalWithdrawal.objects.create(
            user=request.user,
            goal=goal,
            reference=generate_withdrawal_reference(),
            amount=amount,
            bank_name=serializer.validated_data["bank_name"],
            account_name=serializer.validated_data["account_name"],
            account_number=serializer.validated_data["account_number"],
            status=WithdrawalStatus.PENDING,
        )

    return Response(
        GoalWithdrawalSerializer(withdrawal).data,
        status=status.HTTP_201_CREATED
    )



 #Users withdrwal History

@extend_schema(
    tags=["Withdrawals"],
    summary="List withdrawal requests",
    description="Returns the authenticated user's withdrawal request history.",
    responses={
        200: GoalWithdrawalSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_withdrawals(request):

    withdrawals = GoalWithdrawal.objects.filter(
        user=request.user
    ).select_related(
        "goal"
    ).order_by("-requested_at")

    serializer = GoalWithdrawalSerializer(
        withdrawals,
        many=True
    )

    return Response(serializer.data)

