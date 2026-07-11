"""
Friendship model for Facebook Clone.
Tracks friend requests between users with status (pending/accepted/rejected).
"""
from django.conf import settings
from django.db import models


class Friendship(models.Model):
    """Friendship/friend request between two users."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"

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
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("from_user", "to_user")
        verbose_name_plural = "Friendships"

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"

    def accept(self):
        """Accept the friend request."""
        self.status = self.Status.ACCEPTED
        self.save()
        # Create reverse friendship
        Friendship.objects.get_or_create(
            from_user=self.to_user,
            to_user=self.from_user,
            defaults={"status": self.Status.ACCEPTED},
        )
        # Update the ManyToMany friends field on CustomUser
        self.from_user.friends.add(self.to_user)

    def reject(self):
        """Reject the friend request."""
        self.status = self.Status.REJECTED
        self.save()
