"""
Friendship views: send request, accept, reject, list friends, suggestions.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from .models import Friendship


class FriendRequestView(LoginRequiredMixin, View):
    """Send a friend request."""

    def post(self, request, *args, **kwargs):
        to_user = get_object_or_404(
            get_user_model(),
            username=kwargs["username"],
        )
        if to_user != request.user:
            Friendship.objects.get_or_create(
                from_user=request.user,
                to_user=to_user,
                defaults={"status": "pending"},
            )
        return redirect(request.META.get("HTTP_REFERER", "home"))


class FriendAcceptView(LoginRequiredMixin, View):
    """Accept a friend request."""

    def post(self, request, *args, **kwargs):
        friendship = get_object_or_404(
            Friendship,
            id=kwargs["pk"],
            to_user=request.user,
            status="pending",
        )
        friendship.accept()
        return redirect(request.META.get("HTTP_REFERER", "friend_requests"))


class FriendRejectView(LoginRequiredMixin, View):
    """Reject a friend request."""

    def post(self, request, *args, **kwargs):
        friendship = get_object_or_404(
            Friendship,
            id=kwargs["pk"],
            to_user=request.user,
            status="pending",
        )
        friendship.reject()
        return redirect(request.META.get("HTTP_REFERER", "friend_requests"))


class FriendRemoveView(LoginRequiredMixin, View):
    """Remove a friend."""

    def post(self, request, *args, **kwargs):
        friend = get_object_or_404(
            get_user_model(),
            username=kwargs["username"],
        )
        # Remove both directions
        Friendship.objects.filter(
            Q(from_user=request.user, to_user=friend) |
            Q(from_user=friend, to_user=request.user),
            status="accepted",
        ).delete()
        request.user.friends.remove(friend)
        return redirect(request.META.get("HTTP_REFERER", "friend_list"))


class FriendListView(LoginRequiredMixin, ListView):
    """List all friends of the current user."""
    template_name = "friendships/friend_list.html"
    context_object_name = "friends"

    def get_queryset(self):
        return self.request.user.friends.all()


class FriendRequestsView(LoginRequiredMixin, ListView):
    """Show pending friend requests received by current user."""
    template_name = "friendships/friend_requests.html"
    context_object_name = "friend_requests"

    def get_queryset(self):
        return Friendship.objects.filter(
            to_user=self.request.user,
            status="pending",
        ).select_related("from_user")


class SentRequestsView(LoginRequiredMixin, ListView):
    """Show pending friend requests sent by current user."""
    template_name = "friendships/sent_requests.html"
    context_object_name = "sent_requests"

    def get_queryset(self):
        return Friendship.objects.filter(
            from_user=self.request.user,
            status="pending",
        ).select_related("to_user")


class FriendSuggestionsView(LoginRequiredMixin, TemplateView):
    """Show friend suggestions: users who are not already friends."""
    template_name = "friendships/friend_suggestions.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()

        # IDs of existing connections (friends + pending)
        friend_ids = set(self.request.user.friends.values_list("id", flat=True))
        sent_ids = set(Friendship.objects.filter(
            from_user=self.request.user
        ).values_list("to_user_id", flat=True))
        received_ids = set(Friendship.objects.filter(
            to_user=self.request.user
        ).values_list("from_user_id", flat=True))

        exclude_ids = friend_ids | sent_ids | received_ids | {self.request.user.id}

        # Suggest users not already connected
        suggestions = User.objects.exclude(id__in=exclude_ids)[:20]
        context["suggestions"] = suggestions
        context["suggestion_count"] = suggestions.count()
        return context
