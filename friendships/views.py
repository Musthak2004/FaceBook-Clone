from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import ListView, View

from django_ratelimit.decorators import ratelimit

from accounts.models import CustomUser
from notifications.models import Notification
from .models import Friendship


class FriendRequestListView(LoginRequiredMixin, ListView):
    template_name = "friendships/friend_requests.html"
    context_object_name = "requests"

    def get_queryset(self):
        return Friendship.objects.filter(
            to_user=self.request.user, status="pending"
        ).select_related("from_user")


@method_decorator(ratelimit(key="ip", rate="10/m", method="POST"), name="dispatch")
class SendRequestView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        to_user = get_object_or_404(CustomUser, pk=self.kwargs["pk"])
        if request.user == to_user:
            return JsonResponse(
                {"error": "Cannot send request to yourself"}, status=400
            )

        friendship, created = Friendship.objects.get_or_create(
            from_user=request.user, to_user=to_user, defaults={"status": "pending"}
        )

        if not created:
            return JsonResponse({"error": "Request already exists"}, status=400)

        # Create notification
        Notification.objects.create(
            recipient=to_user,
            sender=request.user,
            notification_type="friend_request",
        )

        return JsonResponse({"sent": True})


class AcceptRequestView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        friendship = get_object_or_404(
            Friendship, pk=self.kwargs["pk"], to_user=request.user, status="pending"
        )
        friendship.status = "accepted"
        friendship.save()

        Notification.objects.create(
            recipient=friendship.from_user,
            sender=request.user,
            notification_type="friend_accept",
        )

        return JsonResponse({"accepted": True})


class RejectRequestView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        friendship = get_object_or_404(
            Friendship, pk=self.kwargs["pk"], to_user=request.user, status="pending"
        )
        friendship.status = "rejected"
        friendship.save()
        return JsonResponse({"rejected": True})


class RemoveFriendView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        friend = get_object_or_404(CustomUser, pk=self.kwargs["pk"])
        friendship = Friendship.objects.filter(
            from_user=request.user, to_user=friend, status="accepted"
        ).first()
        if not friendship:
            friendship = Friendship.objects.filter(
                from_user=friend, to_user=request.user, status="accepted"
            ).first()
        if friendship:
            friendship.delete()
            return JsonResponse({"removed": True})
        return JsonResponse({"error": "Not friends"}, status=400)


class BlockUserView(LoginRequiredMixin, View):
    """Block a user — removes any existing friendship."""

    def post(self, request, *args, **kwargs):
        to_block = get_object_or_404(CustomUser, pk=self.kwargs["pk"])
        if request.user == to_block:
            return JsonResponse({"error": "Cannot block yourself"}, status=400)

        # Remove any existing friendship in either direction
        Friendship.objects.filter(
            Q(from_user=request.user, to_user=to_block)
            | Q(from_user=to_block, to_user=request.user)
        ).delete()

        # Create blocked record
        Friendship.objects.create(
            from_user=request.user, to_user=to_block, status="blocked"
        )
        return JsonResponse({"blocked": True})


class UnblockUserView(LoginRequiredMixin, View):
    """Unblock a previously blocked user."""

    def post(self, request, *args, **kwargs):
        to_unblock = get_object_or_404(CustomUser, pk=self.kwargs["pk"])
        deleted, _ = Friendship.objects.filter(
            from_user=request.user, to_user=to_unblock, status="blocked"
        ).delete()
        if deleted:
            return JsonResponse({"unblocked": True})
        return JsonResponse({"error": "User was not blocked"}, status=400)
