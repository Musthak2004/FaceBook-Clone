from notifications.models import Notification


def notification_count(request):
    """Make notification count available to all templates."""
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return {
            'unread_notifications_count': unread_count,
        }
    return {}
