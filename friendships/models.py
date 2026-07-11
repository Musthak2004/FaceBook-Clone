from django.conf import settings
from django.db import models
from django.db.models import Q, Count, Exists, OuterRef


class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='friendship_requests_sent'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='friendship_requests_received'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('from_user', 'to_user')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['from_user', 'status']),
            models.Index(fields=['to_user', 'status']),
        ]

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}: {self.status}"

    @classmethod
    def are_friends(cls, user1, user2):
        """Check if two users are friends."""
        return cls.objects.filter(
            Q(from_user=user1, to_user=user2) | Q(from_user=user2, to_user=user1),
            status='accepted',
        ).exists()

    @classmethod
    def get_friend_ids(cls, user):
        """Return list of user IDs that are friends with the given user."""
        sent = cls.objects.filter(
            from_user=user, status='accepted'
        ).values_list('to_user_id', flat=True)
        received = cls.objects.filter(
            to_user=user, status='accepted'
        ).values_list('from_user_id', flat=True)
        return list(sent) + list(received)

    @classmethod
    def friend_status(cls, user1, user2):
        """Get the friendship status between two users."""
        if user1 == user2:
            return 'self'
        try:
            f = cls.objects.get(
                Q(from_user=user1, to_user=user2) |
                Q(from_user=user2, to_user=user1)
            )
            return f.status
        except cls.DoesNotExist:
            return 'none'

    @classmethod
    def get_suggestions(cls, user, limit=10):
        """Suggest friends-of-friends not already connected."""
        friend_ids = cls.get_friend_ids(user)
        excluded = set(friend_ids)
        excluded.add(user.pk)

        # Also exclude users with pending requests
        pending_sent = cls.objects.filter(
            from_user=user
        ).values_list('to_user_id', flat=True)
        pending_recv = cls.objects.filter(
            to_user=user
        ).values_list('from_user_id', flat=True)
        excluded.update(pending_sent)
        excluded.update(pending_recv)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        # Annotate with mutual friend count
        friend_rel = cls.objects.filter(
            status='accepted',
        ).filter(
            Q(from_user=OuterRef('pk'), to_user__in=friend_ids) |
            Q(to_user=OuterRef('pk'), from_user__in=friend_ids)
        )
        return User.objects.exclude(pk__in=excluded).annotate(
            mutual_count=Count('pk', filter=Q(Exists(friend_rel)))
        ).order_by('-mutual_count')[:limit]
