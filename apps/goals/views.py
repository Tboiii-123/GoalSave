from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import SavingsGoal, GoalStatus
from .serializers import SavingsGoalSerializer,GoalFundingSerializer
from django.db import transaction
from apps.wallet.models import Wallet, WalletTransaction
from apps.ledger.models import (LedgerEntry,LedgerEntryType,LedgerTransactionType)
from .models import (SavingsGoal,GoalStatus,GoalFunding)
from apps.payments.services import generate_reference   
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)


@extend_schema(
    tags=["Goals"],
    summary="Create a savings goal",
    description="Creates a new savings goal for the authenticated user.",
    request=SavingsGoalSerializer,
    responses={
        201: SavingsGoalSerializer,
        400: OpenApiResponse(description="Validation error"),
    },
    examples=[
        OpenApiExample(
            "Create Goal",
            request_only=True,
            value={
                "title": "Buy Laptop",
                "target_amount": 500000,
                "target_date": "2026-12-31",
            },
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_goal(request):
    serializer = SavingsGoalSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@extend_schema(
    tags=["Goals"],
    summary="List savings goals",
    description="Returns all savings goals belonging to the authenticated user.",
    responses={200: SavingsGoalSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_goals(request):
    goals = SavingsGoal.objects.select_related("user").filter(user=request.user).order_by("-created_at")
    

    serializer = SavingsGoalSerializer(goals, many=True)

    return Response(serializer.data)



@extend_schema(
    tags=["Goals"],
    summary="Retrieve a savings goal",
    description="Returns the details of a specific savings goal owned by the authenticated user.",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Savings Goal UUID",
        )
    ],
    responses={
        200: SavingsGoalSerializer,
        404: OpenApiResponse(description="Goal not found"),
        403: OpenApiResponse(description="Access denied"),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def retrieve_goal(request, pk):
    try:
        goal = SavingsGoal.objects.select_related("user").get(id=pk)
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if goal.user != request.user:
        return Response(
            {"detail": "Only the owner can access this goal."},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = SavingsGoalSerializer(goal)

    return Response(serializer.data)







@extend_schema(
    tags=["Goals"],
    summary="Delete a savings goal",
    description=(
        "Deletes a savings goal. "
        "A goal cannot be deleted if it contains saved funds."
    ),
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Savings Goal UUID",
        )
    ],
    responses={
        200: OpenApiResponse(description="Goal deleted successfully"),
        400: OpenApiResponse(description="Goal contains saved funds"),
        404: OpenApiResponse(description="Goal not found"),
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_goal(request, pk):
    try:
        goal = SavingsGoal.objects.get(
            id=pk,
            user=request.user
        )
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if goal.user != request.user:
        return Response(
            {"detail": "Only the owner can delete this goal."},
            status=status.HTTP_403_FORBIDDEN
        )


    if goal.saved_amount > 0:
        return Response(
            {
                "detail": "Cannot delete a goal with saved funds."
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    goal.delete()

    return Response(
        {"detail": "Goal deleted successfully."},
          status=status.HTTP_200_OK
    )


@extend_schema(
    tags=["Goals"],
    summary="Pause a savings goal",
    description="Changes the status of a savings goal to PAUSED.",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Savings Goal UUID",
        )
    ],
    responses={
        200: OpenApiResponse(description="Goal paused successfully"),
        404: OpenApiResponse(description="Goal not found"),
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def pause_goal(request, pk):
    try:
        goal = SavingsGoal.objects.get(
            id=pk,
            user=request.user
        )
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if goal.user != request.user:
        return Response(
            {"detail": "Only the owner can pause this goal."},
            status=status.HTTP_403_FORBIDDEN
        )

    goal.status = GoalStatus.PAUSED
    goal.save(update_fields=["status"])

    return Response({"detail": "Goal paused successfully."})


@extend_schema(
    tags=["Goals"],
    summary="Resume a savings goal",
    description="Changes the status of a paused savings goal back to ACTIVE.",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Savings Goal UUID",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Goal resumed successfully"),
        404: OpenApiResponse(description="Goal not found"),
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def resume_goal(request, pk):
    try:
        goal = SavingsGoal.objects.get(
            id=pk,
            user=request.user
        )
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    if goal.user != request.user:
        return Response(
            {"detail": "Only the owner can resume this goal."},
            status=status.HTTP_403_FORBIDDEN
        )

    goal.status = GoalStatus.ACTIVE
    goal.save(update_fields=["status"])

    return Response({"detail": "Goal resumed successfully."})

@extend_schema(
    tags=["Goals"],
    summary="Complete a savings goal",
    description="Marks a savings goal as completed.",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Savings Goal UUID",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Goal marked as completed"),
        404: OpenApiResponse(description="Goal not found"),
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def complete_goal(request, pk):
    try:
        goal = SavingsGoal.objects.get(
            id=pk,
            user=request.user
        )
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    if goal.user != request.user:
        return Response(
            {"detail": "Only the owner can mark_complete this goal."},
            status=status.HTTP_403_FORBIDDEN
        )

    goal.status = GoalStatus.COMPLETED
    goal.save(update_fields=["status"])

    return Response({"detail": "Goal marked as completed."})


@extend_schema(
    tags=["Goals"],
    summary="Fund a savings goal",
    description=(
        "Transfers money from the authenticated user's wallet "
        "into one of their savings goals."
    ),
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Savings Goal UUID",
        ),
    ],
    request=GoalFundingSerializer,
    responses={
        200: OpenApiResponse(description="Goal funded successfully"),
        400: OpenApiResponse(
            description=(
                "Validation error, insufficient balance, "
                "goal paused, or goal already completed."
            )
        ),
        404: OpenApiResponse(description="Goal not found"),
    },
    examples=[
        OpenApiExample(
            "Fund Goal",
            request_only=True,
            value={
                "amount": 5000
            },
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def fund_goal(request, pk):

    serializer = GoalFundingSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    amount = serializer.validated_data["amount"]

    with transaction.atomic():

        wallet = Wallet.objects.select_for_update().get(
            user=request.user
        )

        goal = get_object_or_404(
            SavingsGoal.objects.select_for_update(),
            id=pk,
            user=request.user
        )

        if goal.status == GoalStatus.PAUSED:
            return Response(
                {"detail": "Goal is currently paused."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if goal.status == GoalStatus.COMPLETED:
            return Response(
                {"detail": "Goal is already completed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if wallet.available_balance < amount:
            return Response(
                {"detail": "Insufficient wallet balance."},
                status=status.HTTP_400_BAD_REQUEST
            )

        balance_before = wallet.available_balance

        # Debit wallet
        wallet.available_balance -= amount
        wallet.save(update_fields=["available_balance"])

        balance_after = wallet.available_balance

        # Credit goal
        goal.saved_amount += amount

        if goal.saved_amount >= goal.target_amount:
            goal.status = GoalStatus.COMPLETED

        goal.save()

        reference = generate_reference()

        # Goal funding history
        GoalFunding.objects.create(
            wallet=wallet,
            goal=goal,
            reference=reference,
            amount=amount
        )

        # Wallet transaction
        WalletTransaction.objects.create(
            wallet=wallet,
            reference=reference,
            transaction_type="TRANSFER",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            status="SUCCESS",
            description=f"Transferred to goal: {goal.name}"
        )

        # Ledger entry
        LedgerEntry.objects.create(
            wallet=wallet,
            transaction_reference=reference,
            transaction_type=LedgerTransactionType.TRANSFER,
            entry_type=LedgerEntryType.DEBIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=f"Transfer to savings goal: {goal.name}"
        )

    return Response(
        {
            "message": "Goal funded successfully.",
            "wallet_balance": wallet.available_balance,
            "goal_saved": goal.saved_amount,
            "goal_status": goal.status,
        },
        status=status.HTTP_200_OK
    )