from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import LedgerEntry
from .serializers import LedgerEntrySerializer
from apps.accounts.models import User


from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)



#Admin enpoint
@extend_schema(
    tags=["Admin"],
    summary="List ledger entries",
    description="Returns all ledger entries ordered by the most recent first.",
    responses={
        200: LedgerEntrySerializer(many=True),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_ledger_entries(request):

    entries = LedgerEntry.objects.select_related("wallet","wallet__user").order_by("-created_at")

    serializer = LedgerEntrySerializer(
        entries,
        many=True
    )

    return Response(serializer.data)





@extend_schema(
    tags=["Admin"],
    summary="List a user's ledger entries",
    description="Returns all ledger entries belonging to a specific user.",
    parameters=[
        OpenApiParameter(
            name="user_id",
            type=str,
            location=OpenApiParameter.PATH,
            description="User ID",
        ),
    ],
    responses={
        200: LedgerEntrySerializer(many=True),
        404: OpenApiResponse(description="User not found"),
    },
)
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


@extend_schema(
    tags=["Admin"],
    summary="Retrieve a ledger entry",
    description="Returns the details of a specific ledger entry.",
    parameters=[
        OpenApiParameter(
            name="pk",
            type=str,
            location=OpenApiParameter.PATH,
            description="Ledger entry ID",
        ),
    ],
    responses={
        200: LedgerEntrySerializer,
        404: OpenApiResponse(description="Ledger entry not found"),
    },
)
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