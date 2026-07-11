"""
App config for notifications. Wires signal handlers for notification creation
and auto-creates NotificationPreference on User creation.
"""
from django.apps import AppConfig
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notifications"

    def ready(self):
        # Import signals module to register @receiver decorators (email sender)
        import notifications.signals  # noqa

        # Auto-create NotificationPreference on User signup
        from .models import create_notification_preference
        User_model = get_user_model()
        post_save.connect(
            create_notification_preference,
            sender=User_model,
            weak=False,
        )

        # Connect action → notification signals
        self._connect_action_signals()

    @staticmethod
    def _connect_action_signals():
        """Wire notification-creation handlers to Like, Comment, Friendship post_save."""
        from django.db.models.signals import post_save
        from .signals import notify_like, notify_comment
        from .signals import notify_friend_request, notify_friend_accept

        try:
            from posts.models import Like, Comment
            post_save.connect(notify_like, sender=Like, weak=False)
            post_save.connect(notify_comment, sender=Comment, weak=False)
        except ImportError:
            pass

        try:
            from friendships.models import Friendship
            post_save.connect(notify_friend_request, sender=Friendship, weak=False)
            post_save.connect(notify_friend_accept, sender=Friendship, weak=False)
        except ImportError:
            pass
