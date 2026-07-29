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
from apps.withdrawal.models import GoalWithdrawal, WithdrawalStatus
from apps.withdrawal.serializers import GoalWithdrawalSerializer
from apps.accounts.models import User
from .permissions import  IsSuperAdmin,IsFinanceAdmin,IsSupportAdmin
from .serializers import AdminUserSerializer




#Admin - Get  Withdrawals with filters status 
@api_view(["GET"])
@permission_classes([IsSuperAdmin])
def list_withdrawals(request):

    withdrawals = GoalWithdrawal.objects.select_related(
        "user",
        "goal"
    ).order_by("-requested_at")

    status_filter = request.GET.get("status")

    if status_filter:
        withdrawals = withdrawals.filter(
            status=status_filter.upper()
        )

    user_id = request.GET.get("user")

    if user_id:
        withdrawals = withdrawals.filter(
            user_id=user_id
        )

    serializer = GoalWithdrawalSerializer(
        withdrawals,
        many=True
    )

    return Response(serializer.data)


@api_view(["PATCH"])
@permission_classes([IsSuperAdmin])
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




#Reject withdrwal
@api_view(["PATCH"])
@permission_classes([IsSuperAdmin])
def reject_withdrawal(request, pk):

    with transaction.atomic():

        withdrawal = get_object_or_404(
            GoalWithdrawal.objects.select_for_update(),
            pk=pk
        )

        if withdrawal.status != WithdrawalStatus.PENDING:
            return Response(
                {
                    "detail": "Withdrawal has already been processed."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        remarks = request.data.get("remarks")

        withdrawal.status = WithdrawalStatus.REJECTED
        withdrawal.remarks = remarks
        withdrawal.processed_at = timezone.now()

        withdrawal.save(
            update_fields=[
                "status",
                "remarks",
                "processed_at"
            ]
        )

    return Response(
        {
            "detail": "Withdrawal rejected successfully."
        },
        status=status.HTTP_200_OK
    )


#Get a simgle withdrawal
@api_view(["GET"])
@permission_classes([IsSuperAdmin])
def retrieve_admin_withdrawal(request, pk):

    withdrawal = get_object_or_404(
        GoalWithdrawal.objects.select_related(
            "user",
            "goal"
        ),
        pk=pk
    )

    serializer = GoalWithdrawalSerializer(
        withdrawal
    )

    return Response(serializer.data)




# PATCH  /api/admin/withdrawals/<id>/reject/

# GET    /api/admin/dashboard/

# GET    /api/admin/deposits/



#     POST   /api/admin/create-users/
@api_view(["POST"])
@permission_classes([IsSuperAdmin])
def create_user(request):

    serializer = AdminUserSerializer(
        data=request.data
    )

    serializer.is_valid(
        raise_exception=True
    )

    serializer.save()

    return Response(
        serializer.data,
        status=status.HTTP_201_CREATED
    )



#     PATCH   /api/admin/update-users/

@api_view(["PATCH"])
@permission_classes([IsSuperAdmin])
def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    serializer = AdminUserSerializer(
        instance=user,
        data=request.data,
        partial=True
    )

    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(
        serializer.data,
        status=status.HTTP_200_OK
    )


from django.db.models import Q



# GET    /api/admin/users/
@api_view(["GET"])
@permission_classes([IsSuperAdmin])
def list_users(request):

    users = User.objects.select_related(
        "profile"
    ).order_by("-created_at")

    search = request.GET.get("search")

    role = request.GET.get("role")

    approved = request.GET.get("approved")

    suspended = request.GET.get("suspended")

    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )

    if role:
        users = users.filter(
            role=role.upper()
        )

    if approved:
        users = users.filter(
            is_approved=approved.lower() == "true"
        )

    if suspended:
        users = users.filter(
            is_suspended=suspended.lower() == "true"
        )

    serializer = AdminUserSerializer(
        users,
        many=True
    )

    return Response(serializer.data)


#DELETE /api/admin/users/<uuid:user_id>/

@api_view(["DELETE"])
@permission_classes([IsSuperAdmin])
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    user.delete()

    return Response(
        {"message": "User deleted successfully."},
        status=status.HTTP_200_OK
    )