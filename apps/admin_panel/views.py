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
from .serializers import AdminUserSerializer,RejectWithdrawalSerializer,WithdrawalApprovalResponseSerializer,AdminMessageSerializer

from apps.utils.cache import get_or_set_cache,invalidate_cache,invalidate_withdrawal_cache


from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)


#Admin - Get  Withdrawals with filters status 
@extend_schema(
    tags=["Admin"],
    summary="List withdrawal requests",
    description="Returns all withdrawal requests with optional filtering by status or user.",
    parameters=[
        OpenApiParameter(
            name="status",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by withdrawal status (PENDING, SUCCESS, REJECTED).",
            required=False,
        ),
        OpenApiParameter(
            name="user",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by user ID.",
            required=False,
        ),
    ],
    responses={
        200: GoalWithdrawalSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsSuperAdmin])
def list_withdrawals(request):

    status_filter = request.GET.get("status")
    user_id = request.GET.get("user")

    cache_key = (
        f"admin:withdrawals:"
        f"status:{status_filter or 'all'}:"
        f"user:{user_id or 'all'}"
    )

    def fetch_withdrawals():
        withdrawals = GoalWithdrawal.objects.select_related(
            "user",
            "goal"
        ).order_by("-requested_at")

        if status_filter:
            withdrawals = withdrawals.filter(
                status=status_filter.upper()
            )

        if user_id:
            withdrawals = withdrawals.filter(
                user_id=user_id
            )

        serializer = GoalWithdrawalSerializer(
            withdrawals,
            many=True
        )

        return serializer.data

    data = get_or_set_cache(
        cache_key,
        fetch_withdrawals,
        timeout=300,
    )

    return Response(data)

@extend_schema(
    tags=["Admin"],
    summary="Approve a withdrawal",
    description="Approves a pending withdrawal request, debits the savings goal, records a ledger entry, and marks the withdrawal as successful.",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Withdrawal ID",
        ),
    ],
    request=None,
    responses={
        200: WithdrawalApprovalResponseSerializer,
        400: AdminMessageSerializer,
        404: AdminMessageSerializer,
    },
)
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

        invalidate_withdrawal_cache()

    return Response(
        {
            "detail": "Withdrawal approved successfully.",
            "reference": withdrawal.reference,
            "status": withdrawal.status
        },
        status=status.HTTP_200_OK
    )





#Reject withdrwal
@extend_schema(
    tags=["Admin"],
    summary="Reject a withdrawal",
    description="Rejects a pending withdrawal request and optionally stores admin remarks.",
     request=RejectWithdrawalSerializer,
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Withdrawal ID",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Withdrawal rejected successfully"),
        400: OpenApiResponse(description="Withdrawal already processed"),
        404: OpenApiResponse(description="Withdrawal not found"),
    },
)
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

        invalidate_withdrawal_cache()

    return Response(
        {
            "detail": "Withdrawal rejected successfully."
        },
        status=status.HTTP_200_OK
    )


#Get a simgle withdrawal
@extend_schema(
    tags=["Admin"],
    summary="Retrieve a withdrawal",
    description="Returns the details of a specific withdrawal request.",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Withdrawal ID",
        ),
    ],
    responses={
        200: GoalWithdrawalSerializer,
        404: OpenApiResponse(description="Withdrawal not found"),
    },
)
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


@extend_schema(
    tags=["Admin"],
    summary="Create a user",
    description="Creates a new user account.",
    request=AdminUserSerializer,
    responses={
        201: AdminUserSerializer,
        400: OpenApiResponse(description="Validation error"),
    },
)
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

@extend_schema(
    tags=["Admin"],
    summary="Update a user",
    description="Updates an existing user's information.",
    request=AdminUserSerializer,
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="User ID",
        ),
    ],
    responses={
        200: AdminUserSerializer,
        404: OpenApiResponse(description="User not found"),
    },
)
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
@extend_schema(
    tags=["Admin"],
    summary="List users",
    description="Returns all users with optional filtering by search, role, approval status, and suspension status.",
    parameters=[
        OpenApiParameter(
            name="search",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Search by email, username, first name, or last name.",
            required=False,
        ),
        OpenApiParameter(
            name="role",
            type=str,
            location=OpenApiParameter.QUERY,
            description="Filter by user role.",
            required=False,
        ),
        OpenApiParameter(
            name="approved",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Filter by approval status.",
            required=False,
        ),
        OpenApiParameter(
            name="suspended",
            type=bool,
            location=OpenApiParameter.QUERY,
            description="Filter by suspension status.",
            required=False,
        ),
    ],
    responses={
        200: AdminUserSerializer(many=True),
    },
)
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

@extend_schema(
    tags=["Admin"],
    summary="Delete a user",
    description="Deletes a user account.",
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="User ID",
        ),
    ],
    responses={
        200: OpenApiResponse(description="User deleted successfully"),
        404: OpenApiResponse(description="User not found"),
    },
)
@api_view(["DELETE"])
@permission_classes([IsSuperAdmin])
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    user.delete()

    return Response(
        {"message": "User deleted successfully."},
        status=status.HTTP_200_OK
    )