"""
URL patterns for notifications app.
Namespace: notifications
"""
from django.urls import path
from .views import (
    NotificationListView,
    NotificationMarkReadView,
    NotificationMarkAllReadView,
    NotificationPreferencesView,
)

app_name = "notifications"

urlpatterns = [
    path("", NotificationListView.as_view(), name="list"),
    path(
        "mark-read/<int:pk>/",
        NotificationMarkReadView.as_view(),
        name="mark_read",
    ),
    path(
        "mark-all-read/",
        NotificationMarkAllReadView.as_view(),
        name="mark_all_read",
    ),
    path(
        "preferences/",
        NotificationPreferencesView.as_view(),
        name="preferences",
    ),
]
