"""
Notification and NotificationPreference models.
Uses GenericForeignKey for polymorphic target references.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    """A notification for a user about an action performed by another user."""

    VERB_CHOICES = [
        ("liked_your_post", "Liked your post"),
        ("commented_on_your_post", "Commented on your post"),
        ("sent_friend_request", "Sent you a friend request"),
        ("accepted_friend_request", "Accepted your friend request"),
        ("mentioned_you", "Mentioned you"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions",
    )
    verb = models.CharField(max_length=50, choices=VERB_CHOICES)
    # GenericForeignKey for polymorphic target referencing
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    target_object_id = models.PositiveIntegerField(
        null=True, blank=True, db_index=True,
    )
    target = GenericForeignKey("target_content_type", "target_object_id")

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"{self.recipient.username} - {self.verb} by {actor_name}"


class NotificationPreference(models.Model):
    """Per-user notification preferences, one-to-one with User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    # Email preferences per notification type
    email_likes = models.BooleanField(default=True)
    email_comments = models.BooleanField(default=True)
    email_friend_requests = models.BooleanField(default=True)
    email_mentions = models.BooleanField(default=True)
    # Push (in-app/WebSocket) preferences per notification type
    push_likes = models.BooleanField(default=True)
    push_comments = models.BooleanField(default=True)
    push_friend_requests = models.BooleanField(default=True)
    push_mentions = models.BooleanField(default=True)

    def __str__(self):
        return f"Notification preferences for {self.user.username}"


def create_notification_preference(sender, instance, created, **kwargs):
    """Auto-create NotificationPreference when a new User is created."""
    if created:
        NotificationPreference.objects.get_or_create(user=instance)
