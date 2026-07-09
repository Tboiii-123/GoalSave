import uuid
import requests
import hmac
import hashlib
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.conf import settings
from .models import DepositTransaction, PaymentGateway,PaymentStatus
from apps.wallet.models import Wallet,WalletTransaction
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from apps.ledger.models import LedgerEntry,LedgerEntryType,LedgerTransactionType

PAYSTACK_INIT_URL = "https://api.paystack.co/transaction/initialize"
PAYSTACK_VERIFY_URL = "https://api.paystack.co/transaction/verify/"


def generate_reference():
    return f"DEP_{uuid.uuid4().hex[:10].upper()}"


def initialize_paystack_payment(user, wallet, amount):
    reference = generate_reference()

    # Create pending transaction first (important for idempotency later)
    deposit = DepositTransaction.objects.create(
        user=user,
        wallet=wallet,
        reference=reference,
        gateway_reference=reference,  
        gateway=PaymentGateway.PAYSTACK,
        amount=amount,
    )

    payload = {
        "email": user.email,
        "amount": int(amount * 100),  # Paystack uses kobo
        "reference": reference,
        "callback_url": "http://localhost:8000/api/payments/verify/" + reference,
    }

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(PAYSTACK_INIT_URL, json=payload, headers=headers)
    data = response.json()

    if not data.get("status"):
        deposit.status = "FAILED"
        deposit.gateway_response = data
        deposit.save()
        return None

    return {
        "authorization_url": data["data"]["authorization_url"],
        "access_code": data["data"]["access_code"],
        "reference": reference,
    }




#Webhook config


def verify_paystack_signature(request):
    paystack_signature = request.headers.get("x-paystack-signature")
    print("Secret:", settings.PAYSTACK_SECRET_KEY)
    print("Headers:", request.headers)

    if not paystack_signature:
        return False

    body = request.body

    secret = settings.PAYSTACK_SECRET_KEY.encode()


    computed_hash = hmac.new(
        secret,
        body,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(computed_hash, paystack_signature)





#Webhook View
#Payment Webhook
# Why AllowAny?

# Because Paystack isn't one of your users. It doesn't have a JWT token.

# Instead of trusting logged-in users, you trust Paystack by verifying its signature.

from decimal import Decimal

@api_view(["POST"])
@permission_classes([AllowAny])
def paystack_webhook(request):

    # Debugging (remove in production)
    print("WEBHOOK HIT")
    print(request.headers)
    print(request.body)

    # Verify Paystack signature
    if not verify_paystack_signature(request):
        return Response(
            {"detail": "Invalid signature"},
            status=status.HTTP_400_BAD_REQUEST
        )

    payload = json.loads(request.body)

    event = payload.get("event")
    data = payload.get("data", {})

    # Ignore events we don't care about
    if event != "charge.success":
        return Response(
            {"detail": "Ignored event"},
            status=status.HTTP_200_OK
        )

    reference = data.get("reference")

    with transaction.atomic():

        # Idempotency check
        if DepositTransaction.objects.filter(
            reference=reference,
            status=PaymentStatus.SUCCESS
        ).exists():
            return Response(
                {"detail": "Already processed"},
                status=status.HTTP_200_OK
            )

        # Lock the deposit row
        deposit = DepositTransaction.objects.select_for_update().filter(
            reference=reference
        ).first()

        if not deposit:
            return Response(
                {"detail": "Deposit not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Use database amount (Decimal)
        amount = deposit.amount

        # Lock the wallet row
        wallet = Wallet.objects.select_for_update().get(
            id=deposit.wallet.id
        )

        balance_before = wallet.available_balance

        # Credit wallet
        wallet.available_balance += amount
        wallet.total_funded += amount
        wallet.save()

        balance_after = wallet.available_balance

        # Mark deposit as successful
        deposit.status = PaymentStatus.SUCCESS
        deposit.gateway_reference = str(data.get("id"))
        deposit.gateway_response = data
        deposit.save()

        # Record wallet transaction
        WalletTransaction.objects.create(
            wallet=wallet,
            reference=reference,
            transaction_type="DEPOSIT",
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            status="SUCCESS",
            description="Wallet funded via Paystack"
        )

        LedgerEntry.objects.create(
            wallet=wallet,
            transaction_reference=reference,
            transaction_type=LedgerTransactionType.DEPOSIT,
            entry_type=LedgerEntryType.CREDIT,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description="Wallet credited via Paystack deposit"
            
)

    return Response(
        {"status": "success"},
        status=status.HTTP_200_OK
    )