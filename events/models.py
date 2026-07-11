"""
Event and Attendee models for public events with RSVP.
"""
from django.conf import settings
from django.db import models
from django.urls import reverse


class Event(models.Model):
    """A public event with date, location, and RSVP tracking."""

    title = models.CharField(max_length=200)
    description = models.TextField(max_length=2000, blank=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    cover = models.ImageField(
        upload_to="event_covers/",
        blank=True,
        null=True,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"pk": self.pk})


class Attendee(models.Model):
    """RSVP linking a user to an event with a status."""

    class Status(models.TextChoices):
        GOING = "going", "Going"
        MAYBE = "maybe", "Maybe"
        NOT_GOING = "not_going", "Not Going"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="attendees",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_rsvps",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.GOING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "user")

    def __str__(self):
        return f"{self.user.username} @ {self.event.title} ({self.status})"


# Auto-cleanup cover image on event delete via post_delete signal
def delete_event_cover(sender, instance, **kwargs):
    """Remove the cover image file from disk when event is deleted."""
    if instance.cover:
        instance.cover.delete(save=False)
