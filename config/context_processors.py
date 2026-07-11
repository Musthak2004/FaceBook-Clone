def notification_count(request):
    """Context processor for unread notification count.
    Full implementation added in Phase 6 (Notifications)."""
    if request.user.is_authenticated:
        return {'unread_notifications_count': 0}
    return {}
