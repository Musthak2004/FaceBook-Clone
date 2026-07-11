"""
Notification views: list, mark-read, and preferences.
Uses Django for Beginners patterns (LoginRequiredMixin, ListView, UpdateView).
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, FormView
from django.contrib.contenttypes.prefetch import GenericPrefetch

from .models import Notification, NotificationPreference
from .forms import NotificationPreferenceForm


class NotificationListView(LoginRequiredMixin, ListView):
    """Paginated list of the current user's notifications."""

    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user,
        ).select_related("actor").prefetch_related(
            GenericPrefetch(
                "target",
                [
                    # Polymorphic targets — prefetch each content type
                ],
            ),
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unread_count"] = Notification.objects.filter(
            recipient=self.request.user, is_read=False,
        ).count()
        return context


class NotificationMarkReadView(LoginRequiredMixin, UpdateView):
    """Mark a single notification as read. POST only."""

    model = Notification
    fields = []
    http_method_names = ["post"]

    def get_object(self, queryset=None):
        obj = get_object_or_404(
            Notification,
            pk=self.kwargs["pk"],
            recipient=self.request.user,
        )
        return obj

    def form_valid(self, form):
        self.object.is_read = True
        self.object.save(update_fields=["is_read"])
        return redirect(self.get_success_url())

    def get_success_url(self):
        return self.request.META.get(
            "HTTP_REFERER",
            reverse_lazy("notifications:list"),
        )


class NotificationMarkAllReadView(LoginRequiredMixin, UpdateView):
    """Mark all unread notifications as read. POST only."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        Notification.objects.filter(
            recipient=request.user, is_read=False,
        ).update(is_read=True)
        return redirect(
            request.META.get(
                "HTTP_REFERER",
                reverse_lazy("notifications:list"),
            )
        )


class NotificationPreferencesView(LoginRequiredMixin, FormView):
    """View and update notification preferences."""

    form_class = NotificationPreferenceForm
    template_name = "notifications/preferences_form.html"
    success_url = reverse_lazy("notifications:preferences")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        pref, _ = NotificationPreference.objects.get_or_create(
            user=self.request.user,
        )
        kwargs["instance"] = pref
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)
