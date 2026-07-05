from django.conf import settings
from django.db import models
from django.urls import reverse


class Event(models.Model):
    """An event with date, location, and attendees."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_events",
    )
    cover = models.ImageField(upload_to="event_covers/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("events:detail", kwargs={"pk": self.pk})

    @property
    def attendee_count(self):
        return self.attendees.count()


class Attendee(models.Model):
    """Tracks RSVP status for an event."""

    GOING = "going"
    MAYBE = "maybe"
    NOT_GOING = "not_going"

    STATUS_CHOICES = [
        (GOING, "Going"),
        (MAYBE, "Maybe"),
        (NOT_GOING, "Not Going"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="event_rsvps",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="attendees",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=GOING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "event")

    def __str__(self):
        return f"{self.user.username} — {self.event.title} ({self.status})"
