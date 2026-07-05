from django.conf import settings
from django.db import models
from django.db.models import Q


class Friendship(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("blocked", "Blocked"),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendship_requests_sent",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friendship_requests_received",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("from_user", "to_user")
        ordering = ["-created_at"]
        verbose_name_plural = "Friendships"

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"

    @classmethod
    def are_friends(cls, user1, user2):
        return cls.objects.filter(
            Q(from_user=user1, to_user=user2) | Q(from_user=user2, to_user=user1),
            status="accepted",
        ).exists()

    @classmethod
    def get_friends(cls, user):
        from_user_friends = cls.objects.filter(
            from_user=user, status="accepted"
        ).values_list("to_user", flat=True)
        to_user_friends = cls.objects.filter(
            to_user=user, status="accepted"
        ).values_list("from_user", flat=True)
        return list(from_user_friends) + list(to_user_friends)

    @classmethod
    def get_mutual_friends(cls, user1, user2):
        friends1 = set(cls.get_friends(user1))
        friends2 = set(cls.get_friends(user2))
        return list(friends1 & friends2)

    @classmethod
    def friend_status(cls, user1, user2):
        if user1 == user2:
            return "self"
        try:
            friendship = cls.objects.get(
                Q(from_user=user1, to_user=user2) | Q(from_user=user2, to_user=user1)
            )
            return friendship.status
        except cls.DoesNotExist:
            return "none"
