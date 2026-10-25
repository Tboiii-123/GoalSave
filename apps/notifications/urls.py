
from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.list_notifications, name="list"),
    path("unread-count/",views.unread_notification_count,name="unread-count"),
    path("read-all/",views.mark_all_notifications_read,name="read-all"),
    path("<uuid:notification_id>/read/",views.mark_notification_read,name="mark-read"),
    path("<uuid:notification_id>/",views.delete_notification,name="delete"),
]