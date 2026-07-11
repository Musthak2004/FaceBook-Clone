"""Site-wide context processors."""
from django.db.models import Q
from friendships.models import Friendship


def site_context(request):
    """Context available to all templates."""
    context = {}
    if request.user.is_authenticated:
        # Friend request count
        context["pending_request_count"] = Friendship.objects.filter(
            to_user=request.user,
            status="pending",
        ).count()
        # Unread notification count (for navbar badge)
        try:
            from notifications.models import Notification
            context["unread_notifications"] = Notification.objects.filter(
                recipient=request.user, is_read=False,
            ).count()
        except Exception:
            context["unread_notifications"] = 0
    return context
