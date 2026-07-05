"""Middleware to track user online status via last_seen."""

from datetime import timedelta

from django.utils import timezone


class UpdateLastSeenMiddleware:
    """Update request.user.last_seen on each request (throttled to 1 min)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            # Only update DB if more than 1 min since last update
            if not request.user.last_seen or now - request.user.last_seen > timedelta(
                minutes=1
            ):
                # Use update() to avoid unnecessary save() signals
                from accounts.models import CustomUser

                CustomUser.objects.filter(pk=request.user.pk).update(last_seen=now)
                request.user.last_seen = now
        return self.get_response(request)
