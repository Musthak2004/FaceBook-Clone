"""Views for the Groups app."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View

from .forms import GroupForm
from .models import Group, GroupMembership, GroupPost


class GroupListView(LoginRequiredMixin, ListView):
    """List all groups — public directory."""

    model = Group
    template_name = "groups/group_list.html"
    context_object_name = "groups"
    paginate_by = 20

    def get_queryset(self):
        return Group.objects.all().select_related("admin")


class GroupCreateView(LoginRequiredMixin, CreateView):
    """Create a new group (creator becomes admin)."""

    model = Group
    form_class = GroupForm
    template_name = "groups/group_form.html"
    success_url = reverse_lazy("groups:group_list")

    def form_valid(self, form):
        form.instance.admin = self.request.user
        response = super().form_valid(form)
        # Auto-join the creator as admin
        GroupMembership.objects.create(
            user=self.request.user, group=self.object, role="admin"
        )
        return response


class GroupDetailView(LoginRequiredMixin, DetailView):
    """Show a single group and its posts."""

    model = Group
    template_name = "groups/group_detail.html"
    context_object_name = "group"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context["posts"] = group.posts.select_related("author").all()
        context["is_member"] = group.memberships.filter(user=self.request.user).exists()
        return context


class GroupJoinLeaveView(LoginRequiredMixin, View):
    """AJAX endpoint to join or leave a group."""

    def post(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=self.kwargs["pk"])

        # Admin cannot leave (must transfer ownership first)
        if group.admin == request.user:
            return JsonResponse(
                {"error": "Group admin cannot leave. Transfer admin first."},
                status=400,
            )

        membership = GroupMembership.objects.filter(user=request.user, group=group)

        if membership.exists():
            # Leave
            membership.delete()
            return JsonResponse({"is_member": False})
        else:
            # Join
            GroupMembership.objects.create(
                user=request.user, group=group, role="member"
            )
            return JsonResponse({"is_member": True})


class GroupPostCreateView(LoginRequiredMixin, View):
    """AJAX endpoint to create a post in a group."""

    def post(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=self.kwargs["pk"])

        # Must be a member
        if not group.memberships.filter(user=request.user).exists():
            return JsonResponse(
                {"error": "You are not a member of this group."}, status=403
            )

        content = request.POST.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Content is required."}, status=400)

        post = GroupPost.objects.create(
            group=group, author=request.user, content=content
        )
        return JsonResponse(
            {
                "created": True,
                "post_id": post.pk,
                "author": post.author.username,
                "content": post.content,
                "created_at": post.created_at.isoformat(),
            }
        )
