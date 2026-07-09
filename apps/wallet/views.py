from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Wallet
from .serializers import ( WalletSerializer, WalletTransactionSerializer)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_wallet(request):
    wallet = get_object_or_404(
        Wallet.objects.select_related("user"),
        user=request.user
    )

    serializer = WalletSerializer(wallet)

    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wallet_transactions(request):
    wallet = get_object_or_404(
        Wallet.objects.prefetch_related("transactions"),
        user=request.user
    )

    serializer = WalletTransactionSerializer(
        wallet.transactions.all(),
        many=True
    )

    return Response(serializer.data)