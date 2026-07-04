from django.db.models.signals import post_save
from django.dispatch import receiver

from comments.models import Comment
from friendships.models import Friendship
from reactions.models import Reaction

from .models import Notification


@receiver(post_save, sender=Friendship)
def create_friendship_notification(sender, instance, created, **kwargs):
    """Create notification when a friend request is sent."""
    if created and instance.status == 'pending':
        Notification.objects.get_or_create(
            recipient=instance.to_user,
            sender=instance.from_user,
            notification_type='friend_request',
        )


@receiver(post_save, sender=Friendship)
def create_friend_accept_notification(sender, instance, **kwargs):
    """Create notification when a friend request is accepted."""
    if instance.status == 'accepted' and not kwargs.get('created', False):
        # Check if notification already exists
        existing = Notification.objects.filter(
            recipient=instance.from_user,
            sender=instance.to_user,
            notification_type='friend_accept',
        ).exists()
        if not existing:
            Notification.objects.create(
                recipient=instance.from_user,
                sender=instance.to_user,
                notification_type='friend_accept',
            )


@receiver(post_save, sender=Reaction)
def create_reaction_notification(sender, instance, created, **kwargs):
    """Create notification when a post is liked."""
    if created and instance.post.author != instance.user:
        Notification.objects.get_or_create(
            recipient=instance.post.author,
            sender=instance.user,
            notification_type='like',
            post=instance.post,
        )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """Create notification when a comment is made."""
    if not created:
        return

    # Notify post author
    if instance.post.author != instance.author:
        Notification.objects.get_or_create(
            recipient=instance.post.author,
            sender=instance.author,
            notification_type='comment',
            post=instance.post,
            comment=instance,
        )

    # Notify parent comment author (for replies)
    if instance.parent and instance.parent.author != instance.author:
        Notification.objects.get_or_create(
            recipient=instance.parent.author,
            sender=instance.author,
            notification_type='reply',
            post=instance.post,
            comment=instance,
        )
