from rest_framework.decorators import api_view, permission_classes,throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import SavingsGoal, GoalStatus,GoalMember,GoalMemberStatus,GoalRole,GoalInvitation,InvitationStatus,GoalShareActivity,GoalShareActivityType
from .serializers import (SavingsGoalSerializer,GoalFundingSerializer,GoalInvitationSerializer,
GoalMemberSerializer,GoalInvitationListSerializer,GoalContributionSerializer,MessageSerializer
,GoalInvitationResponseSerializer,SmartGoalPlannerSerializer,SmartGoalPlanSerializer)
from django.db import transaction
from apps.wallet.models import Wallet, WalletTransaction
from apps.ledger.models import (LedgerEntry,LedgerEntryType,LedgerTransactionType)
from .models import (SavingsGoal,GoalStatus,GoalFunding)
from apps.payments.services import generate_reference   
from apps.accounts.models import User
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)
from django.utils import timezone
from apps.utils.throttles import MessageThrottle,AiThrottle
from apps.utils.cache import get_or_set_cache
from apps.utils.ai import generate_smart_goal_plan

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
                "name": "Buy Laptop",
                "target_amount": 500000,
                "target_date": "2026-12-31",
                  "is_shared": "true",
            },
        ),
    ],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def create_goal(request):
    serializer = SavingsGoalSerializer(data=request.data)

    if serializer.is_valid():

        with transaction.atomic():
            goal = serializer.save(owner=request.user)

            if goal.is_shared:
                GoalMember.objects.create(
                    goal=goal,
                    owner=request.user,
                    role=GoalRole.OWNER,
                )

                GoalShareActivity.objects.create(
    goal=goal,
    user=request.user,
    activity_type=GoalShareActivityType.GOAL_CREATED,
    message=f"{request.user.first_name} created the shared goal."
)

        return Response(
            SavingsGoalSerializer(goal).data,
            status=status.HTTP_201_CREATED,
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=["Goals"],
    summary="List savings goals",
    description="Returns all savings goals belonging to the authenticated user.",
    responses={200: SavingsGoalSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def list_goals(request):

    cache_key = f"goals:{request.user.id}"

    def fetch_goals():
        goals = (
            SavingsGoal.objects
            .select_related("owner")
            .filter(owner=request.user)
            .order_by("-created_at")
        )

        return SavingsGoalSerializer(
            goals,
            many=True,
            context={"request": request},
        ).data

    data = get_or_set_cache(
        key=cache_key,
        fetch_data=fetch_goals,
        timeout=300,
    )

    return Response(data)




@extend_schema(
    tags=["Goals"],
    summary="Retrieve a savings goal",
    description="Returns the details of a specific savings goal owned by the authenticated user.",
    request=None,
    responses={
        200: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def retrieve_goal(request, pk):
    try:
        goal = SavingsGoal.objects.select_related("owner").get(id=pk)
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if goal.owner != request.user:
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
    request=None,
    responses={
        200: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def delete_goal(request, pk):
    try:
        goal = SavingsGoal.objects.get(
            id=pk,
            owner=request.user
        )
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if goal.owner != request.user:
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

    request=None,
    responses={
        200: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def pause_goal(request, pk):
    try:
        goal = SavingsGoal.objects.get(
            id=pk,
            owner=request.user
        )
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if goal.owner != request.user:
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
    request=None,
    responses={
        200: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def resume_goal(request, pk):
    try:
        goal = SavingsGoal.objects.get(
            id=pk,
            owner=request.user
        )
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND
        )
    if goal.owner != request.user:
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
    
    request=None,
    responses={
        200: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def complete_goal(request, pk):
    try:
        goal = SavingsGoal.objects.get(
            id=pk,
            owner=request.user,
        )
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    goal.status = GoalStatus.COMPLETED
    goal.save(update_fields=["status"])

    return Response(
        {"detail": "Goal marked as completed."},
        status=status.HTTP_200_OK,
    )
@extend_schema(
    tags=["Goals"],
    summary="Fund a savings goal",
    description=(
        "Transfers money from the authenticated user's wallet "
        "into one of their savings goals."
    ),
    
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
@throttle_classes([MessageThrottle])
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
        )

        # ===========================
        # Permission Checks
        # ===========================

        if goal.is_shared:

            member = GoalMember.objects.filter(
                goal=goal,
                user=request.user,
            ).first()

            if not member:
                return Response(
                    {
                        "detail": "You are not a member of this shared goal."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if member.role == GoalRole.VIEWER:
                return Response(
                    {
                        "detail": "Viewers cannot fund this goal."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        else:

            if goal.user != request.user:  # Change to goal.owner if renamed
                return Response(
                    {
                        "detail": "You do not own this goal."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # ===========================
        # Goal Status Checks
        # ===========================

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

        # ===========================
        # Wallet Balance Check
        # ===========================

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

        # Goal Funding Record
        GoalFunding.objects.create(
            wallet=wallet,
            user=request.user,  # Add this field to your model
            goal=goal,
            reference=reference,
            amount=amount,
        )
            #Goal Share Activity
        GoalShareActivity.objects.create(
    goal=goal,
    user=request.user,
    activity_type=GoalShareActivityType.CONTRIBUTION,
    message=f"{request.user.first_name} contributed ₦{amount}."
)

        # Wallet Transaction
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

        # Ledger Entry
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
            "contributed_by": request.user.email,
            "amount": amount,
            "wallet_balance": wallet.available_balance,
            "goal_saved": goal.saved_amount,
            "goal_status": goal.status,
        },
        status=status.HTTP_200_OK,
    )

#Goal invite



@extend_schema(
    tags=["Goal Members"],
    summary="Invite a member to a shared goal",
    description=(
        "Allows the owner of a shared savings goal to invite another user "
        "by email. If the email belongs to an existing user, they can later "
        "accept the invitation. Otherwise, the invitation can be used after "
        "registration."
    ),
    request=GoalInvitationSerializer,
    responses={
        201: GoalInvitationResponseSerializer,
        400: MessageSerializer,
        403: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def invite_goal_member(request, pk):
    serializer = GoalInvitationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"]

    try:
        goal = SavingsGoal.objects.get(id=pk)
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Only owner can invite
    if goal.owner != request.user:     
        return Response(
            {"detail": "You are not allowed to invite members to this goal."},
            status=status.HTTP_403_FORBIDDEN,
        )

    # Goal must be shared
    if not goal.is_shared:
        return Response(
            {"detail": "This is not a shared goal."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Already a member?
    if User.objects.filter(email=email).exists():
        invited_user = User.objects.get(email=email)

        if GoalMember.objects.filter(
            goal=goal,
            owner=invited_user
        ).exists():
            return Response(
                {"detail": "This user is already a member of this goal."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # Pending invitation already exists?
    if GoalInvitation.objects.filter(
        goal=goal,
        email=email,
        status=InvitationStatus.PENDING
    ).exists():
        return Response(
            {"detail": "An invitation has already been sent to this email."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        invitation = GoalInvitation.objects.create(
            goal=goal,
            email=email,
            invited_by=request.user,
        )



        # TODO
        # If email belongs to a registered user:
        #   create notification
        #
        # Else:
        #   send signup email
        #
        # In both cases send an invitation email containing:
        # https://goalsave.app/invitations/{invitation.token}

    return Response(
        {
            "message": "Invitation sent successfully.",
            "token": str(invitation.token),   # remove this in production
        },
        status=status.HTTP_201_CREATED,
    )



#Accepts Goal request


@extend_schema(
    tags=["Goal Members"],
    summary="Accept a goal invitation",
    description="Allows a user to accept a pending invitation and join a shared savings goal.",
    request=None,
    parameters=[
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.PATH,
            description="Invitation token",
        ),
    ],
    responses={
        200: MessageSerializer,
        400: MessageSerializer,
        403: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def accept_goal_invitation(request, token):
    try:
        invitation = GoalInvitation.objects.select_related(
            "goal",
            "goal__owner",
        ).get(
            token=token
        )

    except GoalInvitation.DoesNotExist:
        return Response(
            {"detail": "Invitation not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if invitation.status != InvitationStatus.PENDING:
        return Response(
            {"detail": "This invitation is no longer valid."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if invitation.expires_at < timezone.now():

        invitation.status = InvitationStatus.EXPIRED
        invitation.save(update_fields=["status"])

        return Response(
            {"detail": "Invitation has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if request.user.email.lower() != invitation.email.lower():
        return Response(
            {
                "detail": "This invitation was sent to another email address."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if GoalMember.objects.filter(
        goal=invitation.goal,
        owner=request.user,
    ).exists():

        return Response(
            {"detail": "You are already a member of this goal."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():

        GoalMember.objects.create(
            goal=invitation.goal,
            owner=request.user,
            role=GoalRole.CONTRIBUTOR,
        )

        GoalShareActivity.objects.create(
    goal=invitation.goal,
    user=request.user,
    activity_type=GoalShareActivityType.MEMBER_JOINED,
    message=f"{request.user.first_name} joined the goal."
)

        invitation.status = InvitationStatus.ACCEPTED
        invitation.save(update_fields=["status"])

    return Response(
        {
            "message": "You have successfully joined the shared goal."
        },
        status=status.HTTP_200_OK,
    )




@extend_schema(
    tags=["Goal Members"],

    summary="Decline a goal invitation",
    description="Allows a user to decline a pending invitation to a shared savings goal.",
    request=None,
    parameters=[
        OpenApiParameter(
            name="token",
            type=str,
            location=OpenApiParameter.PATH,
            description="Invitation token",
        ),
    ],
    responses={
        200: MessageSerializer,
        400: MessageSerializer,
        403: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])

def decline_goal_invitation(request, token):
    try:
        invitation = GoalInvitation.objects.get(token=token)

    except GoalInvitation.DoesNotExist:
        return Response(
            {"detail": "Invitation not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if invitation.status != InvitationStatus.PENDING:
        return Response(
            {"detail": "This invitation is no longer valid."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if invitation.expires_at < timezone.now():
        invitation.status = InvitationStatus.EXPIRED
        invitation.save(update_fields=["status"])

        return Response(
            {"detail": "Invitation has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if request.user.email.lower() != invitation.email.lower():
        return Response(
            {
                "detail": "This invitation was sent to another email address."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    invitation.status = InvitationStatus.DECLINED
    invitation.save(update_fields=["status"])

    return Response(
        {
            "message": "Invitation declined successfully."
        },
        status=status.HTTP_200_OK,
    )



#Goal Members

@extend_schema(
    tags=["Goal Members"],
    summary="List goal members",
    description="Returns all members of a shared savings goal.",

    request=None,
    responses={
        200: GoalMemberSerializer(many=True),
        403: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def goal_members(request, pk):
    try:
        goal = SavingsGoal.objects.get(pk=pk)

    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not GoalMember.objects.filter(
        goal=goal,
        owner=request.user,
    ).exists():
        return Response(
            {"detail": "You are not a member of this goal."},
            status=status.HTTP_403_FORBIDDEN,
        )

    members = (
        GoalMember.objects
        .filter(goal=goal)
        .select_related("owner")
        .order_by("joined_at")
    )

    serializer = GoalMemberSerializer(members, many=True)

    return Response(serializer.data)


@extend_schema(
    tags=["Goal Members"],
    summary="Remove a goal member",
    description="Allows the owner of a shared goal to remove a member.",

    request=None,
    responses={
        200: MessageSerializer,
        400: MessageSerializer,
        403: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def remove_goal_member(request, goal_id, member_id):
    try:
        goal = SavingsGoal.objects.get(pk=goal_id)
    except SavingsGoal.DoesNotExist:
        return Response(
            {"detail": "Goal not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Only the owner can remove members
    if goal.owner != request.user:   
        return Response(
            {"detail": "Only the goal owner can remove members."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        member = GoalMember.objects.get(
            pk=member_id,
            goal=goal,
        )
    except GoalMember.DoesNotExist:
        return Response(
            {"detail": "Member not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    # Prevent owner from removing themselves
    if member.role == GoalRole.OWNER:
        return Response(
            {"detail": "The owner cannot be removed from the goal."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    member.delete()

    GoalShareActivity.objects.create(
    goal=goal,
    user=member.user,
    activity_type=GoalShareActivityType.MEMBER_REMOVED,
    message=f"{member.user.first_name} was removed from the goal."
)

    return Response(
        {"message": "Member removed successfully."},
        status=status.HTTP_200_OK,
    )


@extend_schema(
    tags=["Goal Members"],
    summary="My pending invitations",
    description="Returns all pending invitations for the authenticated user.",
    request=None,
    responses={
        200: GoalInvitationListSerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def my_goal_invitations(request):

    invitations = (
        GoalInvitation.objects
        .filter(
            email=request.user.email,
            status=InvitationStatus.PENDING,
            expires_at__gt=timezone.now(),
        )
        .select_related("goal", "goal__owner")
        .order_by("-created_at")
    )

    serializer = GoalInvitationListSerializer(
        invitations,
        many=True,
    )

    return Response(serializer.data)


@extend_schema(
    tags=["Goal Members"],
    summary="Goal contribution",
    description="Returns all funding contributions made to a savings goal.",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Savings Goal UUID",
        ),
    ],
    request=None,
    responses={
        200: GoalContributionSerializer(many=True),
        403: MessageSerializer,
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def goal_contributions(request, pk):

    goal = get_object_or_404(
        SavingsGoal,
        pk=pk,
    )

    if goal.is_shared:

        if not GoalMember.objects.filter(
            goal=goal,
            user=request.user,
        ).exists():

            return Response(
                {
                    "detail": "You are not a member of this shared goal."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    else:

        if goal.owner != request.user:      
            return Response(
                {
                    "detail": "You do not own this goal."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

    contributions = (
        GoalFunding.objects
        .filter(goal=goal)
        .select_related("user")
        .order_by("-created_at")
    )

    serializer = GoalContributionSerializer(
        contributions,
        many=True,
    )

    return Response(serializer.data)


@extend_schema(
    tags=["Goal Members"],
    summary="Leave a shared goal",
    description="Allows a contributor to leave a shared savings goal.",
    request=None,
    responses={
        200: MessageSerializer,
        400: MessageSerializer,
        404: MessageSerializer,
    },
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def leave_shared_goal(request, pk):

    goal = get_object_or_404(
        SavingsGoal,
        pk=pk,
    )

    if not goal.is_shared:
        return Response(
            {
                "detail": "This is not a shared goal."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    member = GoalMember.objects.filter(
        goal=goal,
        owner=request.user,
    ).first()

    if not member:
        return Response(
            {
                "detail": "You are not a member of this goal."
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if member.role == GoalRole.OWNER:
        return Response(
            {
                "detail": "The owner cannot leave a shared goal."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    member.delete()

    return Response(
        {
            "message": "You have successfully left the shared goal."
        },
        status=status.HTTP_200_OK,
    )





@extend_schema(
       tags=["Smart AI"],
    request=SmartGoalPlannerSerializer,
    responses={
        200: SmartGoalPlanSerializer,
        502: {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                }
            },
        },
    },
    description=(
        "Uses AI to extract structured savings goal information "
        "from a natural language prompt."
    ),
    summary="Create a smart goal plan",
)
@api_view(["POST"])
@throttle_classes([AiThrottle])
def smart_goal_planner(request):

    input_serializer = SmartGoalPlannerSerializer(
        data=request.data
    )

    input_serializer.is_valid(raise_exception=True)

    prompt = input_serializer.validated_data["prompt"]

    try:
        ai_plan = generate_smart_goal_plan(prompt)

    except Exception:
        return Response(
            {
                "error": "Unable to generate goal plan."
            },
            status=status.HTTP_502_BAD_GATEWAY,
        )

    plan_serializer = SmartGoalPlanSerializer(
        data=ai_plan
    )

    plan_serializer.is_valid(raise_exception=True)

    return Response(
        plan_serializer.validated_data,
        status=status.HTTP_200_OK,
    )