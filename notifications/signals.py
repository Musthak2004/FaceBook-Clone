from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from comments.models import Comment
from friendships.models import Friendship
from reactions.models import Reaction

from .models import Notification


def _send_email_notification(notification):
    """Send a transactional email for high-value notifications."""
    if notification.notification_type not in ("friend_request", "friend_accept"):
        return

    recipient = notification.recipient
    if not recipient.email:
        return

    sender_name = notification.sender.username if notification.sender else "Someone"

    subject_map = {
        "friend_request": f"{sender_name} sent you a friend request on SocialNet",
        "friend_accept": f"{sender_name} accepted your friend request on SocialNet",
    }

    template_map = {
        "friend_request": "emails/friend_request.txt",
        "friend_accept": "emails/friend_accept.txt",
    }

    subject = subject_map.get(
        notification.notification_type, "Notification from SocialNet"
    )
    template_name = template_map.get(notification.notification_type)

    if template_name:
        message = render_to_string(
            template_name,
            {
                "recipient": recipient,
                "sender": notification.sender,
                "site_url": f"{'https' if not settings.DEBUG else 'http'}://"
                f"{settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else '127.0.0.1:8000'}",
            },
        )
    else:
        message = f"You have a new notification from {sender_name} on SocialNet."

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient.email],
        fail_silently=True,
    )


def _push_notification(notification):
    """Send a real-time notification via WebSocket channel layer and email."""
    _send_email_notification(notification)
    channel_layer = get_channel_layer()
    group_name = f"notifications_{notification.recipient_id}"
    unread_count = Notification.objects.filter(
        recipient=notification.recipient, is_read=False
    ).count()

    sender_username = notification.sender.username if notification.sender else ""
    sender_picture = (
        notification.sender.profile_picture.url
        if notification.sender and notification.sender.profile_picture
        else ""
    )

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "notification_message",
            "notification_id": notification.id,
            "notification_type": notification.notification_type,
            "sender_username": sender_username,
            "sender_profile_picture": sender_picture,
            "unread_count": unread_count,
            "message": str(notification),
        },
    )


def _create_notification(**kwargs):
    """Create a notification and push it via WebSocket.

    Respects the recipient's notification preferences — if they've opted
    out of this notification_type, it is silently skipped.
    """
    notification_type = kwargs.get("notification_type")
    recipient = kwargs.get("recipient")

    # Check recipient's preferences before creating the notification
    if recipient and notification_type:
        from .models import NotificationPreference

        prefs = NotificationPreference.get_or_create_for_user(recipient)
        if not prefs.is_enabled(notification_type):
            return None, False

    notification, created = Notification.objects.get_or_create(**kwargs)
    if created:
        _push_notification(notification)
    return notification, created


@receiver(post_save, sender=Friendship)
def create_friendship_notification(sender, instance, created, **kwargs):
    """Create notification when a friend request is sent."""
    if created and instance.status == "pending":
        _create_notification(
            recipient=instance.to_user,
            sender=instance.from_user,
            notification_type="friend_request",
        )


@receiver(post_save, sender=Friendship)
def create_friend_accept_notification(sender, instance, **kwargs):
    """Create notification when a friend request is accepted."""
    if instance.status == "accepted" and not kwargs.get("created", False):
        _create_notification(
            recipient=instance.from_user,
            sender=instance.to_user,
            notification_type="friend_accept",
        )


@receiver(post_save, sender=Reaction)
def create_reaction_notification(sender, instance, created, **kwargs):
    """Create notification when a post is liked."""
    if created and instance.post.author != instance.user:
        _create_notification(
            recipient=instance.post.author,
            sender=instance.user,
            notification_type="like",
            post=instance.post,
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """Create notification when a comment is made."""
    if not created:
        return

    # Notify post author
    if instance.post.author != instance.author:
        _create_notification(
            recipient=instance.post.author,
            sender=instance.author,
            notification_type="comment",
            post=instance.post,
            comment=instance,
        )

    # Notify parent comment author (for replies)
    if instance.parent and instance.parent.author != instance.author:
        _create_notification(
            recipient=instance.parent.author,
            sender=instance.author,
            notification_type="reply",
            post=instance.post,
            comment=instance,
        )
