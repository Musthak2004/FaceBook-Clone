from django.conf import settings
from django.db import models


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ("friend_request", "Friend Request"),
        ("friend_accept", "Friend Request Accepted"),
        ("like", "Like"),
        ("comment", "Comment"),
        ("reply", "Reply"),
        ("mention", "Mention"),
        ("share", "Share"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        db_index=True,
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES, db_index=True
    )
    post = models.ForeignKey(
        "posts.Post", on_delete=models.CASCADE, null=True, blank=True
    )
    comment = models.ForeignKey(
        "comments.Comment", on_delete=models.CASCADE, null=True, blank=True
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.notification_type} for {self.recipient.username}"


class NotificationPreference(models.Model):
    """Per-user toggle for each notification type."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    friend_request = models.BooleanField(default=True)
    friend_accept = models.BooleanField(default=True)
    like = models.BooleanField(default=True)
    comment = models.BooleanField(default=True)
    reply = models.BooleanField(default=True)
    mention = models.BooleanField(default=True)
    share = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Notification Preference"
        verbose_name_plural = "Notification Preferences"

    def __str__(self):
        return f"Preferences for {self.user.username}"

    def is_enabled(self, notification_type):
        """Check if the given notification type is enabled."""
        return getattr(self, notification_type, True)

    @classmethod
    def get_or_create_for_user(cls, user):
        """Get existing preferences or create default ones (all enabled)."""
        prefs, _ = cls.objects.get_or_create(user=user)
        return prefs
