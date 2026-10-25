
from django.db import transaction

from apps.utils.cache import invalidate_cache
from .models import Notification


def unread_count_cache_key(user_id):
    return f"notifications:unread-count:{user_id}"


def invalidate_notification_cache(user_id):
    """
    Invalidate the unread notification count for one user.
    """
    invalidate_cache(unread_count_cache_key(user_id))


def create_notification(
    *,
    user,
    notification_type,
    title,
    message,
    data=None,
    event_key=None,
):
    """
    Create a notification for a user.

    If event_key is supplied, it prevents duplicate notifications
    for the same user and event.
    """
    defaults = {
        "type": notification_type,
        "title": title,
        "message": message,
        "data": data or {},
    }

    if event_key is not None:
        notification, created = Notification.objects.get_or_create(
            user=user,
            event_key=event_key,
            defaults=defaults,
        )
    else:
        notification = Notification.objects.create(
            user=user,
            **defaults,
        )
        created = True

    if created:
        transaction.on_commit(
            lambda: invalidate_notification_cache(user.pk)
        )

    return notification, created