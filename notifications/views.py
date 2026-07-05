from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, View

from .models import Notification, NotificationPreference


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = "notifications/notification_list.html"
    context_object_name = "notifications"
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "sender"
        )

    def render_to_response(self, context, **response_kwargs):
        # Handle JSON requests (used by the dropdown)
        if self.request.GET.get("format") == "json":
            html = render_to_string(
                "notifications/_notification_dropdown_items.html",
                context,
                request=self.request,
            )
            return JsonResponse({"html": html})

        # Handle count-only requests (used by fallback polling)
        if self.request.GET.get("count"):
            unread_count = self.get_queryset().filter(is_read=False).count()
            return JsonResponse({"unread_count": unread_count})

        return super().render_to_response(context, **response_kwargs)


class MarkReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(
            Notification, pk=self.kwargs["pk"], recipient=request.user
        )
        notification.is_read = True
        notification.save()
        return JsonResponse({"read": True})


class MarkAllReadView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True
        )
        return JsonResponse({"read_all": True})


class NotificationPreferencesView(LoginRequiredMixin, UpdateView):
    """View for users to toggle which notification types they receive."""

    model = NotificationPreference
    template_name = "notifications/preferences.html"
    fields = [
        "friend_request",
        "friend_accept",
        "like",
        "comment",
        "reply",
        "mention",
        "share",
    ]
    success_url = reverse_lazy("notifications:preferences")

    def get_object(self, queryset=None):
        return NotificationPreference.get_or_create_for_user(self.request.user)
