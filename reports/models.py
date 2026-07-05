from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Report(models.Model):
    """User-submitted report for posts, comments, or users."""

    REASON_CHOICES = [
        ("spam", "Spam"),
        ("harassment", "Harassment or bullying"),
        ("hate_speech", "Hate speech"),
        ("nudity", "Nudity or sexual content"),
        ("violence", "Violence or harmful content"),
        ("misinformation", "False information"),
        ("other", "Other"),
    ]

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports_made",
    )

    # Generic FK to any content type (post, comment, user profile)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    description = models.TextField(blank=True, help_text="Optional additional details")
    is_reviewed = models.BooleanField(default=False)
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reporter} reported {self.content_type} #{self.object_id} — {self.reason}"
