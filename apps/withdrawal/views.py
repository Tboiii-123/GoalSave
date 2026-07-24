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



#Admin - Get Pending Withdrawals
@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_pending_withdrawals(request):

    withdrawals = GoalWithdrawal.objects.filter(
        status=WithdrawalStatus.PENDING
    ).select_related(
        "user",
        "goal"
    ).order_by("-requested_at")

    serializer = GoalWithdrawalSerializer(
        withdrawals,
        many=True
    )

    return Response(serializer.data)




@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def approve_withdrawal(request, pk):

    with transaction.atomic():

        # Lock withdrawal row
        withdrawal = get_object_or_404(
            GoalWithdrawal.objects.select_for_update(),
            pk=pk
        )

        # Already processed?
        if withdrawal.status != WithdrawalStatus.PENDING:
            return Response(
                {
                    "detail": "Withdrawal has already been processed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Lock goal row
        goal = SavingsGoal.objects.select_for_update().get(
            id=withdrawal.goal.id
        )

        # Lock wallet row (needed for ledger)
        wallet = Wallet.objects.select_for_update().get(
            user=withdrawal.user
        )

        # Safety check
        if withdrawal.amount > goal.saved_amount:
            return Response(
                {
                    "detail": "Insufficient goal balance."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        balance_before = goal.saved_amount

        # Debit goal
        goal.saved_amount -= withdrawal.amount
        goal.save(
            update_fields=["saved_amount"]
        )

        balance_after = goal.saved_amount

        # Create ledger entry
        LedgerEntry.objects.create(
            wallet=wallet,
            transaction_reference=withdrawal.reference,
            transaction_type=LedgerTransactionType.WITHDRAWAL,
            entry_type=LedgerEntryType.DEBIT,
            amount=withdrawal.amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description="Withdrawal approved and paid to customer's bank account."
        )

        # Mark withdrawal as successful
        withdrawal.status = WithdrawalStatus.SUCCESS
        withdrawal.processed_at = timezone.now()
        withdrawal.save(
            update_fields=[
                "status",
                "processed_at"
            ]
        )

    return Response(
        {
            "detail": "Withdrawal approved successfully.",
            "reference": withdrawal.reference,
            "status": withdrawal.status
        },
        status=status.HTTP_200_OK
    )