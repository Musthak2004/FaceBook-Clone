from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    cover_photo = models.ImageField(upload_to="covers/", blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    date_of_birth = models.DateField(null=True, blank=True)
    education = models.CharField(max_length=255, blank=True)
    work = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    is_private = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)
    friends = models.ManyToManyField(
        "self",
        through="friendships.Friendship",
        symmetrical=False,
        related_name="friend_set",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    def get_absolute_url(self):
        return reverse("profile", kwargs={"username": self.username})

    @property
    def friend_count(self):
        from friendships.models import Friendship

        return Friendship.objects.filter(
            models.Q(from_user=self) | models.Q(to_user=self), status="accepted"
        ).count()

    @property
    def post_count(self):
        return self.posts.filter(is_draft=False).count()

    @property
    def is_online(self):
        """User is considered online if last_seen is within 5 minutes."""
        if not self.last_seen:
            return False
        return timezone.now() - self.last_seen < timedelta(minutes=5)

    @property
    def last_seen_display(self):
        """Human-friendly last seen string."""
        if not self.last_seen:
            return "Never"
        diff = timezone.now() - self.last_seen
        if diff < timedelta(minutes=1):
            return "Just now"
        if diff < timedelta(hours=1):
            mins = int(diff.total_seconds() / 60)
            return f"{mins}m ago"
        if diff < timedelta(days=1):
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        return self.last_seen.strftime("%b %d")
