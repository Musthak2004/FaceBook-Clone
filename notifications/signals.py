"""
Signal handlers for creating notifications from actions and sending email alerts.

Triggers:
  - Post liked (not own) → liked_your_post
  - Post commented (not own) → commented_on_your_post
  - Friend request sent → sent_friend_request
  - Friend request accepted → accepted_friend_request
"""
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model

from .models import Notification, NotificationPreference


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_email_preference(verb):
    """Map a notification verb to the email preference field name."""
    mapping = {
        "liked_your_post": "email_likes",
        "commented_on_your_post": "email_comments",
        "sent_friend_request": "email_friend_requests",
        "accepted_friend_request": "email_friend_requests",
        "mentioned_you": "email_mentions",
    }
    return mapping.get(verb)


def _get_push_preference(verb):
    """Map a notification verb to the push preference field name."""
    mapping = {
        "liked_your_post": "push_likes",
        "commented_on_your_post": "push_comments",
        "sent_friend_request": "push_friend_requests",
        "accepted_friend_request": "push_friend_requests",
        "mentioned_you": "push_mentions",
    }
    return mapping.get(verb)


def _get_verb_display(verb):
    """Short human-readable label for email subject lines."""
    labels = {
        "liked_your_post": "liked your post",
        "commented_on_your_post": "commented on your post",
        "sent_friend_request": "sent you a friend request",
        "accepted_friend_request": "accepted your friend request",
        "mentioned_you": "mentioned you",
    }
    return labels.get(verb, verb)


# ---------------------------------------------------------------------------
# Notification creation signals (wired in apps.py)
# ---------------------------------------------------------------------------

def notify_like(sender, instance, created, **kwargs):
    """Create notification when someone likes a post that isn't their own."""
    if not created:
        return
    if instance.post.author != instance.user:
        Notification.objects.create(
            recipient=instance.post.author,
            actor=instance.user,
            verb="liked_your_post",
            target_content_type=ContentType.objects.get_for_model(instance.post),
            target_object_id=instance.post.pk,
        )


def notify_comment(sender, instance, created, **kwargs):
    """Create notification when someone comments on a post that isn't their own."""
    if not created:
        return
    if instance.post.author != instance.author:
        Notification.objects.create(
            recipient=instance.post.author,
            actor=instance.author,
            verb="commented_on_your_post",
            target_content_type=ContentType.objects.get_for_model(instance.post),
            target_object_id=instance.post.pk,
        )


def notify_friend_request(sender, instance, created, **kwargs):
    """Create notification when a friend request is sent."""
    if not created:
        return
    if instance.status == "pending":
        Notification.objects.create(
            recipient=instance.to_user,
            actor=instance.from_user,
            verb="sent_friend_request",
        )


def notify_friend_accept(sender, instance, created, **kwargs):
    """Create notification when a friend request is accepted.

    This fires for the *reverse* Friendship row created by Friendship.accept().
    In that row, from_user=accepter and to_user=requester, so we notify the
    requester (instance.to_user) that the accepter (instance.from_user) accepted.
    """
    if not created:
        return
    if instance.status == "accepted":
        Notification.objects.create(
            recipient=instance.to_user,
            actor=instance.from_user,
            verb="accepted_friend_request",
        )


# ---------------------------------------------------------------------------
# Email notification — fires on Notification creation only, checks prefs
# ---------------------------------------------------------------------------

@receiver(post_save, sender=Notification)
def send_notification_email(sender, instance, created, **kwargs):
    """Send email notification when a Notification is created, if preference allows."""
    if not created:
        return
    if not instance.recipient.email:
        return

    pref_field = _get_email_preference(instance.verb)
    if not pref_field:
        return

    try:
        pref = NotificationPreference.objects.get(user=instance.recipient)
        if not getattr(pref, pref_field, True):
            return
    except NotificationPreference.DoesNotExist:
        pass  # default to sending

    actor_name = instance.actor.username if instance.actor else "Someone"
    verb_display = _get_verb_display(instance.verb)
    subject = f"FaceClone: {actor_name} {verb_display}"

    message = render_to_string("notifications/email/notification_email.txt", {
        "recipient": instance.recipient,
        "actor_name": actor_name,
        "verb_display": verb_display,
        "notification": instance,
    })

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[instance.recipient.email],
        fail_silently=True,
    )
