from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import LedgerEntry
from .serializers import LedgerEntrySerializer


#Admin enpoint
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_ledger_entries(request):

    entries = LedgerEntry.objects.select_related("wallet","wallet__user").order_by("-created_at")

    serializer = LedgerEntrySerializer(
        entries,
        many=True
    )

    return Response(serializer.data)



from django.shortcuts import get_object_or_404
from apps.accounts.models import User


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_user_ledger_entries(request, user_id):

    user = get_object_or_404(User, id=user_id)

    entries = LedgerEntry.objects.filter( wallet__user=user).select_related("wallet","wallet__user").order_by("-created_at")

    serializer = LedgerEntrySerializer(
        entries,
        many=True
    )

    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def retrieve_ledger_entry(request, pk):

    entry = get_object_or_404(
        LedgerEntry.objects.select_related("wallet"),
        id=pk,
        wallet__user=request.user
    )

    serializer = LedgerEntrySerializer(entry)

    return Response(serializer.data)