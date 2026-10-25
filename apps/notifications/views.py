
from django.db import transaction
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiExample,
)

from apps.utils.cache import get_or_set_cache, invalidate_cache
from apps.utils.throttles import MessageThrottle

from .models import Notification
from .serializers import (
    NotificationSerializer,
    UnreadNotificationCountSerializer,
    MarkAllReadResponseSerializer,
    NotificationMessageSerializer,
)
from .services import (
    unread_count_cache_key,
    invalidate_notification_cache,
)


@extend_schema(
    tags=["Notifications"],
    summary="List notifications",
    description=(
        "Returns notifications for the authenticated user, "
        "newest first. Supports unread filtering and pagination."
    ),
    parameters=[
        OpenApiParameter(
            name="unread",
            type=bool,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Set true to return only unread notifications.",
        ),
        OpenApiParameter(
            name="limit",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Page size, from 1 to 100. Defaults to 20.",
        ),
        OpenApiParameter(
            name="offset",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="Number of notifications to skip.",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Notification list"),
        400: OpenApiResponse(description="Invalid query parameters"),
        401: OpenApiResponse(description="Authentication required"),
    },
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def list_notifications(request):
    unread_param = request.query_params.get("unread")
    if unread_param not in (None, "true", "false"):
        return Response(
            {"detail": "unread must be true or false."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        limit = int(request.query_params.get("limit", 20))
        offset = int(request.query_params.get("offset", 0))
    except (TypeError, ValueError):
        return Response(
            {"detail": "limit and offset must be integers."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not 1 <= limit <= 100 or offset < 0:
        return Response(
            {"detail": "limit must be 1-100 and offset must be >= 0."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    unread_only = unread_param == "true"

    # User-specific queryset prevents cross-user data access.
    queryset = Notification.objects.filter(user=request.user)

    if unread_only:
        queryset = queryset.filter(is_read=False)

    total = queryset.count()
    results = queryset[offset:offset + limit]

    return Response({
        "count": total,
        "limit": limit,
        "offset": offset,
        "results": NotificationSerializer(
            results,
            many=True,
            context={"request": request},
        ).data,
    })


@extend_schema(
    tags=["Notifications"],
    summary="Get unread notification count",
    description="Returns the number of unread notifications for the current user.",
    responses={200: UnreadNotificationCountSerializer},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def unread_notification_count(request):
    cache_key = unread_count_cache_key(request.user.pk)

    count = get_or_set_cache(
        key=cache_key,
        fetch_data=lambda: Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count(),
        timeout=60,
    )

    return Response({"unread_count": count})


@extend_schema(
    tags=["Notifications"],
    summary="Mark notification as read",
    description="Marks one of the authenticated user's notifications as read.",
    responses={
        200: NotificationSerializer,
        404: OpenApiResponse(description="Notification not found"),
    },
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def mark_notification_read(request, notification_id):
    with transaction.atomic():
        notification = (
            Notification.objects
            .select_for_update()
            .filter(user=request.user, pk=notification_id)
            .first()
        )

        if notification is None:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])

            transaction.on_commit(
                lambda: invalidate_notification_cache(request.user.pk)
            )

    return Response(NotificationSerializer(notification).data)


@extend_schema(
    tags=["Notifications"],
    summary="Mark all notifications as read",
    description="Marks every unread notification belonging to the current user as read.",
    responses={200: MarkAllReadResponseSerializer},
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def mark_all_notifications_read(request):
    now = timezone.now()

    with transaction.atomic():
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).update(
            is_read=True,
            read_at=now,
        )

        if updated:
            transaction.on_commit(
                lambda: invalidate_notification_cache(request.user.pk)
            )

    return Response({"updated_count": updated})


@extend_schema(
    tags=["Notifications"],
    summary="Delete a notification",
    description="Deletes a notification belonging to the authenticated user.",
    responses={
        204: OpenApiResponse(description="Notification deleted"),
        404: OpenApiResponse(description="Notification not found"),
    },
)
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@throttle_classes([MessageThrottle])
def delete_notification(request, notification_id):
    with transaction.atomic():
        notification = Notification.objects.filter(
            user=request.user,
            pk=notification_id,
        ).first()

        if notification is None:
            return Response(
                {"detail": "Notification not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.delete()

        transaction.on_commit(
            lambda: invalidate_notification_cache(request.user.pk)
        )

    return Response(status=status.HTTP_204_NO_CONTENT)