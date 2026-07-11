"""
Event views: list, detail, create, update, delete, RSVP.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.views import View

from .models import Event, Attendee
from .forms import EventForm


class EventListView(LoginRequiredMixin, ListView):
    """List all upcoming events ordered by date."""

    model = Event
    template_name = "events/event_list.html"
    context_object_name = "events"
    paginate_by = 12


class EventDetailView(LoginRequiredMixin, DetailView):
    """Show event details, attendees, and RSVP status."""

    model = Event
    template_name = "events/event_detail.html"
    context_object_name = "event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.get_object()

        # Group attendees by status
        attendees = event.attendees.select_related("user")
        context["going"] = attendees.filter(status=Attendee.Status.GOING)
        context["maybe"] = attendees.filter(status=Attendee.Status.MAYBE)
        context["not_going"] = attendees.filter(status=Attendee.Status.NOT_GOING)

        # Current user's RSVP
        try:
            context["my_rsvp"] = attendees.get(user=self.request.user)
        except Attendee.DoesNotExist:
            context["my_rsvp"] = None

        context["is_creator"] = event.creator == self.request.user
        return context


class EventCreateView(LoginRequiredMixin, CreateView):
    """Create a new event and auto-RSVP the creator."""

    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def form_valid(self, form):
        form.instance.creator = self.request.user
        response = super().form_valid(form)
        # Auto-RSVP the creator as going
        Attendee.objects.get_or_create(
            event=self.object,
            user=self.request.user,
            defaults={"status": Attendee.Status.GOING},
        )
        return response


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit an event. Only the creator can edit."""

    model = Event
    form_class = EventForm
    template_name = "events/event_form.html"

    def test_func(self):
        obj = self.get_object()
        return obj.creator == self.request.user


class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete an event. Only the creator can delete."""

    model = Event
    template_name = "events/event_confirm_delete.html"
    success_url = reverse_lazy("events:list")

    def test_func(self):
        obj = self.get_object()
        return obj.creator == self.request.user


class RSVPUpdateView(LoginRequiredMixin, View):
    """Create or update the current user's RSVP for an event."""

    def post(self, request, *args, **kwargs):
        event = get_object_or_404(Event, pk=kwargs["pk"])
        status = request.POST.get("status", Attendee.Status.GOING)

        Attendee.objects.update_or_create(
            event=event,
            user=request.user,
            defaults={"status": status},
        )
        return redirect(event.get_absolute_url())
