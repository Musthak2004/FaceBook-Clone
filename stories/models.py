from django.conf import settings
from django.db import models
from django.utils import timezone


class Story(models.Model):
    """A 24-hour disappearing image story."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stories",
    )
    image = models.ImageField(upload_to="stories/")
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "stories"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s story — {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @classmethod
    def active_stories(cls):
        """Return all non-expired stories."""
        return cls.objects.filter(expires_at__gt=timezone.now())

    @classmethod
    def stories_grouped_by_user(cls):
        """Return dict of user -> list of active stories."""
        stories = cls.active_stories().select_related("user").order_by("-created_at")
        grouped = {}
        for story in stories:
            grouped.setdefault(story.user, []).append(story)
        return grouped
