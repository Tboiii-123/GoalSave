from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes,throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from apps.utils.throttles import RegisterThrottle,LoginThrottle,MessageThrottle

from apps.wallet.models import Wallet
from .models import DepositTransaction
from .serializers import DepositInitiateSerializer,DepositTransactionSerializer
from .services import initialize_paystack_payment

from drf_spectacular.utils import (
    extend_schema,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiExample,
)






@extend_schema(
    tags=["Payments"],
    summary="Initialize wallet deposit",
    description=(
        "Initializes a Paystack payment for funding the authenticated user's wallet. "
        "Returns the payment authorization URL and transaction reference."
    ),
    request=DepositInitiateSerializer,
    responses={
        201: OpenApiResponse(
            description="Payment initialized successfully"
        ),
        400: OpenApiResponse(
            description="Payment initialization failed or invalid request"
        ),
    },
    examples=[
        OpenApiExample(
            "Initialize Deposit",
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
def initialize_deposit(request):
    serializer = DepositInitiateSerializer(data=request.data)

    if serializer.is_valid():
        amount = serializer.validated_data["amount"]

        wallet = get_object_or_404(Wallet, user=request.user)

        result = initialize_paystack_payment(
            user=request.user,
            wallet=wallet,
            amount=amount
        )

        if not result:
            return Response(
                {"detail": "Payment initialization failed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(result, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    #List depoist history


@extend_schema(
    tags=["Payments"],
    summary="List deposit history",
    description="Returns the authenticated user's deposit transaction history, ordered from newest to oldest.",
    responses={
        200: OpenApiResponse(description="Deposit history retrieved successfully"),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def list_deposits(request):
    deposits = DepositTransaction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    serializer = DepositTransactionSerializer(
    deposits,
    many=True
)

    return Response(serializer.data)

#verify Deposit (Manual Check)

@extend_schema(
    tags=["Payments"],
    summary="Verify deposit",
    description=(
        "Returns the current status and details of a deposit transaction "
        "using its payment reference."
    ),
    parameters=[
        OpenApiParameter(
            name="reference",
            type=str,
            location=OpenApiParameter.PATH,
            description="Deposit transaction reference",
        ),
    ],
    responses={
        200: OpenApiResponse(
            description="Deposit details retrieved successfully"
        ),
        404: OpenApiResponse(
            description="Deposit not found"
        ),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def verify_deposit(request, reference):
    deposit = get_object_or_404(
        DepositTransaction,
        reference=reference,
        user=request.user
    )

    return Response({
        "reference": deposit.reference,
        "status": deposit.status,
        "amount": deposit.amount,
        "gateway_response": deposit.gateway_response,
    })




