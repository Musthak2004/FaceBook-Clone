from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Attendee, Event

User = get_user_model()


class EventModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_event(self):
        event = Event.objects.create(
            title="Test Event",
            description="A test event",
            date=timezone.now() + timezone.timedelta(days=7),
            location="Test Location",
            creator=self.user,
        )
        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.creator, self.user)
        self.assertEqual(event.attendee_count, 0)

    def test_event_str(self):
        event = Event.objects.create(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.user,
        )
        self.assertEqual(str(event), "Test Event")

    def test_event_ordering(self):
        Event.objects.create(
            title="Earlier",
            date=timezone.now() + timezone.timedelta(days=1),
            creator=self.user,
        )
        Event.objects.create(
            title="Later",
            date=timezone.now() + timezone.timedelta(days=2),
            creator=self.user,
        )
        events = Event.objects.all()
        self.assertGreater(
            events[0].date, events[1].date
        )  # newest first (closest to now)

    def test_event_absolute_url(self):
        event = Event.objects.create(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.user,
        )
        url = event.get_absolute_url()
        self.assertIn(str(event.pk), url)


class AttendeeModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other = User.objects.create_user(username="other", password="testpass123")
        self.event = Event.objects.create(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.user,
        )

    def test_create_attendee(self):
        attendee = Attendee.objects.create(
            user=self.other, event=self.event, status=Attendee.GOING
        )
        self.assertEqual(attendee.status, "going")
        self.assertEqual(self.event.attendee_count, 1)

    def test_attendee_str(self):
        attendee = Attendee.objects.create(
            user=self.other, event=self.event, status=Attendee.MAYBE
        )
        self.assertIn(self.other.username, str(attendee))
        self.assertIn(self.event.title, str(attendee))

    def test_unique_together(self):
        Attendee.objects.create(
            user=self.other, event=self.event, status=Attendee.GOING
        )
        with self.assertRaises(Exception):
            Attendee.objects.create(
                user=self.other, event=self.event, status=Attendee.MAYBE
            )

    def test_update_or_replace_rsvp(self):
        Attendee.objects.create(
            user=self.other, event=self.event, status=Attendee.GOING
        )
        attendee, created = Attendee.objects.update_or_create(
            user=self.other,
            event=self.event,
            defaults={"status": Attendee.MAYBE},
        )
        self.assertFalse(created)
        self.assertEqual(attendee.status, Attendee.MAYBE)


class EventViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")
        self.event = Event.objects.create(
            title="Test Event",
            description="A test event description.",
            date=timezone.now() + timezone.timedelta(days=7),
            location="Test Location",
            creator=self.user,
        )

    def test_event_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("events:list"))
        self.assertNotEqual(response.status_code, 200)

    def test_event_list_shows_events(self):
        response = self.client.get(reverse("events:list"))
        self.assertContains(response, "Test Event")

    def test_event_detail_shows_event(self):
        response = self.client.get(
            reverse("events:detail", kwargs={"pk": self.event.pk})
        )
        self.assertContains(response, "Test Event")
        self.assertContains(response, "A test event description.")
        self.assertContains(response, "Test Location")

    def test_event_create_view(self):
        response = self.client.get(reverse("events:create"))
        self.assertEqual(response.status_code, 200)

    def test_event_create_creates_event(self):
        self.client.post(
            reverse("events:create"),
            {
                "title": "New Event",
                "description": "New event description.",
                "date": "2027-01-15T18:00",
                "location": "New Location",
            },
        )
        self.assertEqual(Event.objects.count(), 2)
        # Creator should be auto-RSVPed
        new_event = Event.objects.get(title="New Event")
        self.assertTrue(
            Attendee.objects.filter(
                user=self.user, event=new_event, status=Attendee.GOING
            ).exists()
        )

    def test_event_update_by_creator(self):
        self.client.post(
            reverse("events:edit", kwargs={"pk": self.event.pk}),
            {
                "title": "Updated Event",
                "description": "Updated description.",
                "date": "2027-02-20T19:00",
                "location": "Updated Location",
            },
        )
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Updated Event")

    def test_event_update_by_non_creator_returns_403(self):
        User.objects.create_user(username="other", password="testpass123")
        self.client.login(username="other", password="testpass123")
        response = self.client.post(
            reverse("events:edit", kwargs={"pk": self.event.pk}),
            {"title": "Hacked"},
        )
        self.assertEqual(response.status_code, 403)

    def test_event_delete_by_creator(self):
        response = self.client.post(
            reverse("events:delete", kwargs={"pk": self.event.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Event.objects.count(), 0)

    def test_event_delete_by_non_creator_returns_403(self):
        User.objects.create_user(username="other", password="testpass123")
        self.client.login(username="other", password="testpass123")
        response = self.client.post(
            reverse("events:delete", kwargs={"pk": self.event.pk})
        )
        self.assertEqual(response.status_code, 403)


class RSVPTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.other = User.objects.create_user(username="other", password="testpass123")
        self.client.login(username="testuser", password="testpass123")
        self.event = Event.objects.create(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.other,
        )

    def test_rsvp_requires_login(self):
        self.client.logout()
        response = self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "going"},
            content_type="application/json",
        )
        self.assertNotEqual(response.status_code, 200)

    def test_rsvp_going(self):
        response = self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "going"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "going")
        self.assertTrue(
            Attendee.objects.filter(
                user=self.user, event=self.event, status=Attendee.GOING
            ).exists()
        )

    def test_rsvp_maybe(self):
        response = self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "maybe"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "maybe")

    def test_rsvp_not_going_removes_attendee(self):
        # First RSVP going
        Attendee.objects.create(user=self.user, event=self.event, status=Attendee.GOING)
        # Then change to not going
        response = self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "not_going"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "removed")
        self.assertFalse(
            Attendee.objects.filter(user=self.user, event=self.event).exists()
        )

    def test_rsvp_invalid_status(self):
        response = self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "invalid_status"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_rsvp_nonexistent_event(self):
        response = self.client.post(
            reverse("events:rsvp", kwargs={"pk": 9999}),
            {"status": "going"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
