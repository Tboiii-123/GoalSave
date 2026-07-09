from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.wallet.models import Wallet
from .models import DepositTransaction
from .serializers import DepositInitiateSerializer
from .services import initialize_paystack_payment








@api_view(["POST"])
@permission_classes([IsAuthenticated])
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

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_deposits(request):
    deposits = DepositTransaction.objects.filter(
        user=request.user
    ).order_by("-created_at")

    data = []

    for d in deposits:
        data.append({
            "reference": d.reference,
            "amount": d.amount,
            "status": d.status,
            "gateway": d.gateway,
            "paid_at": d.paid_at,
            "created_at": d.created_at,
        })

    return Response(data)


#verify Deposit (Manual Check)

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




