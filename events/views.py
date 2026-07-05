import json

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    DeleteView,
)
from django.views import View

from .forms import EventForm
from .models import Attendee, Event


class EventListView(LoginRequiredMixin, ListView):
    """Show upcoming and past events."""

    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"
    paginate_by = 20

    def get_queryset(self):
        return Event.objects.all().select_related("creator")


class EventDetailView(LoginRequiredMixin, DetailView):
    """Show event details with RSVP status."""

    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_queryset(self):
        return Event.objects.all().select_related("creator")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        user_attendance = Attendee.objects.filter(
            user=self.request.user, event=event
        ).first()
        context["user_attendance"] = user_attendance
        context["going_attendees"] = event.attendees.filter(
            status=Attendee.GOING
        ).select_related("user")[:20]
        return context


class EventCreateView(LoginRequiredMixin, CreateView):
    """Create a new event."""

    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        # Auto-RSVP the creator as "going"
        Attendee.objects.get_or_create(
            user=self.request.user,
            event=self.object,
            defaults={"status": Attendee.GOING},
        )
        return response

    def get_success_url(self):
        return self.object.get_absolute_url()


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit an event (creator only)."""

    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def test_func(self):
        return self.get_object().creator == self.request.user

    def get_success_url(self):
        return self.object.get_absolute_url()


class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an event (creator only)."""

    model = Event
    success_url = reverse_lazy("events:list")

    def test_func(self):
        return self.get_object().creator == self.request.user


class RSVPView(LoginRequiredMixin, View):
    """AJAX endpoint to RSVP to an event."""

    def post(self, request, pk):
        try:
            event = Event.objects.get(pk=pk)
        except Event.DoesNotExist:
            return JsonResponse({"error": "Event not found."}, status=404)

        data = json.loads(request.body)
        status = data.get("status", Attendee.GOING)

        if status not in dict(Attendee.STATUS_CHOICES):
            return JsonResponse({"error": "Invalid status."}, status=400)

        if status == Attendee.NOT_GOING:
            Attendee.objects.filter(user=request.user, event=event).delete()
            return JsonResponse(
                {"status": "removed", "attendee_count": event.attendee_count}
            )

        attendee, created = Attendee.objects.update_or_create(
            user=request.user,
            event=event,
            defaults={"status": status},
        )
        return JsonResponse(
            {
                "status": attendee.status,
                "created": created,
                "attendee_count": event.attendee_count,
            }
        )
