"""
Admin registration for Notification and NotificationPreference models.
"""
from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin list display with filtering by read status and verb."""
    list_display = ("recipient", "actor", "verb", "is_read", "created_at")
    list_filter = ("is_read", "verb", "created_at")
    search_fields = ("recipient__username", "actor__username")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin list display for notification preferences."""
    list_display = ("user", "email_likes", "email_comments", "push_likes")
    search_fields = ("user__username",)
