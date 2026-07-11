"""
Group views: list, detail, create, and join/leave.
Uses Django for Beginners patterns (LoginRequiredMixin, ListView, CreateView).
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, View
from django.db.models import Count

from .models import Group, GroupMembership
from .forms import GroupCreateForm
from posts.models import Post


class GroupListView(LoginRequiredMixin, ListView):
    """List all public groups."""

    model = Group
    template_name = "groups/group_list.html"
    context_object_name = "groups"
    paginate_by = 12

    def get_queryset(self):
        return Group.objects.annotate(
            member_count=Count("memberships"),
        ).order_by("-created_at")


class GroupDetailView(LoginRequiredMixin, DetailView):
    """Show group details, member list, and group posts."""

    model = Group
    template_name = "groups/group_detail.html"
    context_object_name = "group"

    def get_queryset(self):
        return Group.objects.annotate(
            member_count=Count("memberships"),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context["posts"] = Post.objects.filter(group=group).select_related(
            "author"
        ).prefetch_related("likes", "comments").order_by("-created_at")
        context["members"] = group.members.all()
        context["is_member"] = group.members.filter(
            pk=self.request.user.pk,
        ).exists()
        context["is_admin"] = group.admin == self.request.user
        return context


class GroupCreateView(LoginRequiredMixin, CreateView):
    """Create a new group and become its admin."""

    model = Group
    form_class = GroupCreateForm
    template_name = "groups/group_form.html"

    def form_valid(self, form):
        form.instance.admin = self.request.user
        response = super().form_valid(form)
        GroupMembership.objects.get_or_create(
            group=self.object,
            user=self.request.user,
            defaults={"role": GroupMembership.Role.ADMIN},
        )
        return response


class GroupJoinView(LoginRequiredMixin, View):
    """Toggle join/leave a public group."""

    def post(self, request, *args, **kwargs):
        group = get_object_or_404(Group, pk=kwargs["pk"])
        membership = GroupMembership.objects.filter(
            group=group, user=request.user,
        )
        if membership.exists():
            if group.admin != request.user:
                membership.delete()
        else:
            GroupMembership.objects.create(
                group=group, user=request.user,
            )
        referer = request.META.get("HTTP_REFERER")
        if referer:
            return redirect(referer)
        return redirect("groups:detail", pk=group.pk)
