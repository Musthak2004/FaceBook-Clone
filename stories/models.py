"""
Story model with 24-hour auto-expiry.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


def default_expiry():
    """Default expiry time: 24 hours from now."""
    return timezone.now() + timezone.timedelta(hours=24)


class ActiveStoryManager(models.Manager):
    """Returns only stories that haven't expired yet."""

    def get_queryset(self):
        now = timezone.now()
        return super().get_queryset().filter(expires_at__gt=now)


class Story(models.Model):
    """A photo story that expires 24 hours after creation."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stories",
    )
    image = models.ImageField(
        upload_to="stories/",
        blank=True,
        null=True,
    )
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        default=default_expiry,
    )

    objects = models.Manager()
    active_stories = ActiveStoryManager()

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "stories"

    def __str__(self):
        return f"{self.user.username}: {self.caption[:30] or '(no caption)'}"

    def is_expired(self):
        return timezone.now() >= self.expires_at


# Auto-cleanup image file on story delete via post_delete signal
def delete_story_image(sender, instance, **kwargs):
    """Remove the image file from disk when story is deleted."""
    if instance.image:
        instance.image.delete(save=False)
