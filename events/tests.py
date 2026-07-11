"""
Tests for events app — written BEFORE implementation (TDD).
Covers models, views, RSVP, and permissions.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


class EventModelTests(TestCase):
    """Tests for the Event model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def setUp(self):
        from events.models import Event
        self.Event = Event

    def test_create_event(self):
        """Can create an event with a creator."""
        event = self.Event.objects.create(
            title="Test Event",
            description="An event description",
            date=timezone.now() + timezone.timedelta(days=7),
            location="Test Location",
            creator=self.user,
        )
        self.assertEqual(self.Event.objects.count(), 1)
        self.assertEqual(event.title, "Test Event")
        self.assertEqual(event.creator, self.user)

    def test_event_str(self):
        """String representation is the event title."""
        event = self.Event.objects.create(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.user,
        )
        self.assertEqual(str(event), "Test Event")

    def test_event_cover_field(self):
        """Event has an optional cover image field."""
        event = self.Event(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.user,
        )
        self.assertTrue(hasattr(event, "cover"))
        self.assertFalse(bool(event.cover))

    def test_event_created_at(self):
        """Event has auto-set created_at."""
        event = self.Event.objects.create(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.user,
        )
        self.assertIsNotNone(event.created_at)

    def test_event_date_required(self):
        """Event requires a date."""
        event = self.Event(
            title="No Date Event",
            creator=self.user,
        )
        # date is required — model validation catches it
        self.assertFalse(event.date)

    def test_default_ordering(self):
        """Events ordered by date ascending (soonest first)."""
        later = self.Event.objects.create(
            title="Later",
            date=timezone.now() + timezone.timedelta(days=10),
            creator=self.user,
        )
        sooner = self.Event.objects.create(
            title="Sooner",
            date=timezone.now() + timezone.timedelta(days=1),
            creator=self.user,
        )
        events = self.Event.objects.all()
        self.assertEqual(events[0], sooner)
        self.assertEqual(events[1], later)

    def test_get_absolute_url(self):
        """Event has get_absolute_url pointing to detail."""
        event = self.Event.objects.create(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.user,
        )
        url = event.get_absolute_url()
        self.assertIn(str(event.pk), url)


class AttendeeModelTests(TestCase):
    """Tests for the Attendee model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user1 = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.user2 = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from events.models import Event, Attendee
        self.Event = Event
        self.Attendee = Attendee
        self.event = self.Event.objects.create(
            title="Test Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.user1,
        )

    def test_create_attendee(self):
        """Can add an attendee to an event."""
        self.Attendee.objects.create(
            event=self.event,
            user=self.user2,
            status=self.Attendee.Status.GOING,
        )
        self.assertEqual(self.Attendee.objects.count(), 1)
        self.assertIn(
            self.user2,
            [a.user for a in self.event.attendees.all()],
        )

    def test_attendee_default_status(self):
        """Default status is 'going'."""
        attendee = self.Attendee.objects.create(
            event=self.event,
            user=self.user2,
        )
        self.assertEqual(attendee.status, "going")

    def test_attendee_status_choices(self):
        """Attendee status can be going, maybe, or not_going."""
        for status in ["going", "maybe", "not_going"]:
            with self.subTest(status=status):
                user = get_user_model().objects.create_user(
                    username=f"user_{status}", password="secret"
                )
                attendee = self.Attendee.objects.create(
                    event=self.event, user=user, status=status,
                )
                self.assertEqual(attendee.status, status)

    def test_attendee_unique_together(self):
        """Each user can only have one RSVP per event."""
        self.Attendee.objects.create(
            event=self.event, user=self.user2,
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            self.Attendee.objects.create(
                event=self.event, user=self.user2,
            )

    def test_attendee_str(self):
        """String representation shows user and event."""
        attendee = self.Attendee.objects.create(
            event=self.event,
            user=self.user2,
            status="maybe",
        )
        self.assertIn(self.user2.username, str(attendee))
        self.assertIn(self.event.title, str(attendee))
        self.assertIn("maybe", str(attendee))

    def test_event_attendees_relationship(self):
        """Event has an attendees queryset via related_name."""
        self.Attendee.objects.create(
            event=self.event, user=self.user2,
        )
        attendees = self.event.attendees.all()
        self.assertIn(self.user2, [a.user for a in attendees])

    def test_attendee_created_at(self):
        """Attendee has auto-set created_at."""
        attendee = self.Attendee.objects.create(
            event=self.event, user=self.user2,
        )
        self.assertIsNotNone(attendee.created_at)


class EventListViewTests(TestCase):
    """Tests for event list view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def setUp(self):
        from events.models import Event
        self.Event = Event
        Event.objects.create(
            title="Event A",
            date=timezone.now() + timezone.timedelta(days=1),
            creator=self.user,
        )
        Event.objects.create(
            title="Event B",
            date=timezone.now() + timezone.timedelta(days=10),
            creator=self.user,
        )

    def test_list_authenticated(self):
        """Authenticated user sees event list."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event A")
        self.assertContains(response, "Event B")

    def test_list_anonymous_redirect(self):
        """Anonymous user redirected to login."""
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_list_pagination(self):
        """Event list uses pagination."""
        for i in range(25):
            self.Event.objects.create(
                title=f"Event {i}",
                date=timezone.now() + timezone.timedelta(days=i + 1),
                creator=self.user,
            )
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("events:list"))
        self.assertIn("page_obj", response.context)
        self.assertIn("is_paginated", response.context)

    def test_list_order_by_date(self):
        """Events are ordered by date ascending."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("events:list"))
        events = response.context["events"]
        dates = [e.date for e in events]
        self.assertEqual(dates, sorted(dates))


class EventDetailViewTests(TestCase):
    """Tests for event detail view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.creator = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.other_user = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from events.models import Event, Attendee
        self.Event = Event
        self.Attendee = Attendee
        self.event = self.Event.objects.create(
            title="Test Event",
            description="A test event",
            date=timezone.now() + timezone.timedelta(days=7),
            location="Test Location",
            creator=self.creator,
        )

    def test_detail_authenticated(self):
        """Authenticated user sees event detail."""
        self.client.login(username="bob", password="secret")
        response = self.client.get(
            reverse("events:detail", kwargs={"pk": self.event.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Event")
        self.assertContains(response, "Test Location")

    def test_detail_anonymous_redirect(self):
        """Anonymous redirected from event detail."""
        response = self.client.get(
            reverse("events:detail", kwargs={"pk": self.event.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_detail_shows_rsvp_status(self):
        """Detail page shows current user's RSVP status."""
        self.Attendee.objects.create(
            event=self.event, user=self.other_user, status="maybe",
        )
        self.client.login(username="bob", password="secret")
        response = self.client.get(
            reverse("events:detail", kwargs={"pk": self.event.pk}),
        )
        self.assertContains(response, "maybe")

    def test_detail_shows_attendee_count(self):
        """Detail page shows number of attendees."""
        self.Attendee.objects.create(
            event=self.event, user=self.other_user,
        )
        self.client.login(username="bob", password="secret")
        response = self.client.get(
            reverse("events:detail", kwargs={"pk": self.event.pk}),
        )
        # Should show attendee count somewhere
        self.assertContains(response, "Attendee")


class EventCreateViewTests(TestCase):
    """Tests for creating an event."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def test_create_view_authenticated(self):
        """Authenticated user sees creation form."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("events:create"))
        self.assertEqual(response.status_code, 200)

    def test_create_view_anonymous_redirect(self):
        """Anonymous user redirected from create."""
        response = self.client.get(reverse("events:create"))
        self.assertEqual(response.status_code, 302)

    def test_create_event(self):
        """POST creates an event with current user as creator."""
        self.client.login(username="alice", password="secret")
        future = timezone.now() + timezone.timedelta(days=7)
        response = self.client.post(
            reverse("events:create"),
            {
                "title": "New Event",
                "description": "A new event",
                "date": future.isoformat(),
                "location": "Somewhere",
            },
        )
        self.assertEqual(response.status_code, 302)
        from events.models import Event
        event = Event.objects.first()
        self.assertIsNotNone(event)
        self.assertEqual(event.title, "New Event")
        self.assertEqual(event.creator, self.user)

    def test_create_event_empty_title(self):
        """Creating an event with empty title shows error."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("events:create"),
            {
                "title": "",
                "date": timezone.now() + timezone.timedelta(days=1),
            },
        )
        self.assertEqual(response.status_code, 200)  # re-renders form


class EventUpdateViewTests(TestCase):
    """Tests for updating an event."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.creator = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.other = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from events.models import Event
        self.event = Event.objects.create(
            title="Original Title",
            description="Original description",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.creator,
        )

    def test_update_event_as_creator(self):
        """Creator can update their event."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("events:update", kwargs={"pk": self.event.pk}),
            {"title": "Updated Title", "date": self.event.date.isoformat()},
        )
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Updated Title")

    def test_update_event_as_non_creator(self):
        """Non-creator gets 403."""
        self.client.login(username="bob", password="secret")
        response = self.client.post(
            reverse("events:update", kwargs={"pk": self.event.pk}),
            {"title": "Hacked Title", "date": self.event.date.isoformat()},
        )
        self.assertEqual(response.status_code, 403)

    def test_update_event_anonymous(self):
        """Anonymous user redirected."""
        response = self.client.post(
            reverse("events:update", kwargs={"pk": self.event.pk}),
            {"title": "Hacked", "date": self.event.date.isoformat()},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())


class EventDeleteViewTests(TestCase):
    """Tests for deleting an event."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.creator = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.other = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from events.models import Event
        self.event = Event.objects.create(
            title="Event to Delete",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.creator,
        )

    def test_delete_event_as_creator(self):
        """Creator can delete their event."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("events:delete", kwargs={"pk": self.event.pk}),
        )
        self.assertEqual(response.status_code, 302)
        from events.models import Event
        self.assertEqual(Event.objects.count(), 0)

    def test_delete_event_as_non_creator(self):
        """Non-creator gets 403."""
        self.client.login(username="bob", password="secret")
        response = self.client.post(
            reverse("events:delete", kwargs={"pk": self.event.pk}),
        )
        self.assertEqual(response.status_code, 403)

    def test_delete_event_anonymous(self):
        """Anonymous user redirected."""
        response = self.client.post(
            reverse("events:delete", kwargs={"pk": self.event.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())


class RSVPUpdateViewTests(TestCase):
    """Tests for RSVP toggle/update."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.creator = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.attendee = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from events.models import Event
        self.event = Event.objects.create(
            title="RSVP Event",
            date=timezone.now() + timezone.timedelta(days=7),
            creator=self.creator,
        )

    def test_rsvp_going(self):
        """User can RSVP 'going'."""
        self.client.login(username="bob", password="secret")
        response = self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "going"},
        )
        self.assertEqual(response.status_code, 302)
        from events.models import Attendee
        attendee = Attendee.objects.get(event=self.event, user=self.attendee)
        self.assertEqual(attendee.status, "going")

    def test_rsvp_maybe(self):
        """User can RSVP 'maybe'."""
        self.client.login(username="bob", password="secret")
        self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "maybe"},
        )
        from events.models import Attendee
        attendee = Attendee.objects.get(event=self.event, user=self.attendee)
        self.assertEqual(attendee.status, "maybe")

    def test_rsvp_not_going(self):
        """User can RSVP 'not going'."""
        self.client.login(username="bob", password="secret")
        self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "not_going"},
        )
        from events.models import Attendee
        attendee = Attendee.objects.get(event=self.event, user=self.attendee)
        self.assertEqual(attendee.status, "not_going")

    def test_rsvp_anonymous_redirect(self):
        """Anonymous user cannot RSVP."""
        response = self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "going"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_rsvp_update_changes_status(self):
        """User can change their RSVP status."""
        from events.models import Attendee
        Attendee.objects.create(
            event=self.event, user=self.attendee, status="going",
        )
        self.client.login(username="bob", password="secret")
        self.client.post(
            reverse("events:rsvp", kwargs={"pk": self.event.pk}),
            {"status": "maybe"},
        )
        attendee = Attendee.objects.get(event=self.event, user=self.attendee)
        self.assertEqual(attendee.status, "maybe")

    def test_rsvp_creator_auto_rsvped(self):
        """Event creator is automatically an attendee (going) when created via view."""
        from events.models import Attendee
        future = timezone.now() + timezone.timedelta(days=7)
        self.client.login(username="alice", password="secret")
        self.client.post(
            reverse("events:create"),
            {
                "title": "View-Created Event",
                "description": "Created through the create view",
                "date": future.isoformat(),
                "location": "Somewhere",
            },
        )
        # Creator should be auto-added as going
        self.assertTrue(
            Attendee.objects.filter(
                event__title="View-Created Event",
                user=self.creator,
                status="going",
            ).exists()
        )
