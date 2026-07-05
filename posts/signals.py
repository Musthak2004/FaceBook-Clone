"""Signal handlers for post processing — hashtag parsing and @mention notifications."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from notifications.models import Notification
from notifications.signals import _push_notification

from .models import Post, Tag
from .utils import parse_hashtags, parse_mentions


@receiver(post_save, sender=Post)
def process_post_content(sender, instance, created, **kwargs):
    """Parse hashtags and @mentions when a post is created.

    - Creates ``Tag`` records for any ``#hashtag`` found in the content.
    - Creates ``mention`` notifications for any ``@username`` that matches an
      existing user (excluding the post author themselves).
    """
    if not created:
        return

    content = instance.content

    # --- Hashtags ---
    tags = parse_hashtags(content)
    if tags:
        tag_objs = [Tag.objects.get_or_create(name=t)[0] for t in tags]
        instance.tags.add(*tag_objs)

    # --- @mentions ---
    mentions = parse_mentions(content)
    if mentions:
        mentioned_users = instance.author.__class__.objects.filter(
            username__in=list(mentions)
        )
        for user in mentioned_users:
            if user == instance.author:
                continue
            notification, created = Notification.objects.get_or_create(
                recipient=user,
                sender=instance.author,
                notification_type="mention",
                post=instance,
            )
            if created:
                _push_notification(notification)

    # --- Share notification ---
    if instance.shared_post and instance.shared_post.author != instance.author:
        notification, created = Notification.objects.get_or_create(
            recipient=instance.shared_post.author,
            sender=instance.author,
            notification_type="share",
            post=instance.shared_post,
        )
        if created:
            _push_notification(notification)
