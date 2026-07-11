from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, View

from accounts.models import CustomUser
from .models import Friendship


class FriendRequestView(LoginRequiredMixin, View):
    """Send a friend request to another user."""

    def post(self, request, user_id):
        to_user = get_object_or_404(CustomUser, pk=user_id)
        if request.user == to_user:
            messages.error(request, "You cannot send a friend request to yourself.")
            return redirect('accounts:profile', username=to_user.username)

        status = Friendship.friend_status(request.user, to_user)
        if status == 'pending':
            messages.info(request, "Friend request already sent.")
        elif status == 'accepted':
            messages.info(request, "You are already friends with this user.")
        elif status == 'rejected':
            Friendship.objects.filter(
                Q(from_user=request.user, to_user=to_user) |
                Q(from_user=to_user, to_user=request.user)
            ).delete()
            Friendship.objects.create(from_user=request.user, to_user=to_user)
            messages.success(request, f"Friend request sent to {to_user.get_full_name()}.")
        else:
            Friendship.objects.create(from_user=request.user, to_user=to_user)
            messages.success(request, f"Friend request sent to {to_user.get_full_name()}.")

        return redirect('accounts:profile', username=to_user.username)


class AcceptFriendRequestView(LoginRequiredMixin, View):
    """Accept a received friend request."""

    def post(self, request, request_id):
        friendship = get_object_or_404(
            Friendship, pk=request_id, to_user=request.user, status='pending'
        )
        friendship.status = 'accepted'
        friendship.save()
        messages.success(
            request,
            f"You are now friends with {friendship.from_user.get_full_name()}."
        )
        return redirect('friendships:friend_requests')


class RejectFriendRequestView(LoginRequiredMixin, View):
    """Reject a received friend request."""

    def post(self, request, request_id):
        friendship = get_object_or_404(
            Friendship, pk=request_id, to_user=request.user, status='pending'
        )
        friendship.status = 'rejected'
        friendship.save()
        messages.info(request, "Friend request rejected.")
        return redirect('friendships:friend_requests')


class CancelFriendRequestView(LoginRequiredMixin, View):
    """Cancel a sent friend request."""

    def post(self, request, request_id):
        friendship = get_object_or_404(
            Friendship, pk=request_id, from_user=request.user, status='pending'
        )
        friendship.delete()
        messages.info(request, "Friend request cancelled.")
        return redirect('friendships:friend_requests')


class UnfriendView(LoginRequiredMixin, View):
    """Remove a friend."""

    def post(self, request, user_id):
        to_user = get_object_or_404(CustomUser, pk=user_id)
        Friendship.objects.filter(
            Q(from_user=request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=request.user),
            status='accepted',
        ).delete()
        messages.success(request, f"Unfriended {to_user.get_full_name()}.")
        return redirect('accounts:profile', username=to_user.username)


class FriendListView(LoginRequiredMixin, ListView):
    """List all friends of the current user."""
    template_name = 'friendships/friend_list.html'
    context_object_name = 'friends'

    def get_queryset(self):
        user_ids = Friendship.get_friend_ids(self.request.user)
        return CustomUser.objects.filter(pk__in=user_ids)


class FriendRequestsView(LoginRequiredMixin, ListView):
    """List pending friend requests received by the current user."""
    template_name = 'friendships/friend_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return Friendship.objects.filter(
            to_user=self.request.user, status='pending'
        ).select_related('from_user')


class SentRequestsView(LoginRequiredMixin, ListView):
    """List pending friend requests sent by the current user."""
    template_name = 'friendships/sent_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return Friendship.objects.filter(
            from_user=self.request.user, status='pending'
        ).select_related('to_user')


class FriendSuggestionsView(LoginRequiredMixin, ListView):
    """Suggest friends for the current user."""
    template_name = 'friendships/friend_suggestions.html'
    context_object_name = 'suggestions'

    def get_queryset(self):
        return Friendship.get_suggestions(self.request.user)
