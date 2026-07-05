from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import ListView, TemplateView, View

from accounts.models import CustomUser
from posts.models import Post
from comments.models import Comment
from .models import Report


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        from django.shortcuts import redirect

        return redirect("core:home")


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/dashboard_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_users"] = CustomUser.objects.count()
        context["total_posts"] = Post.objects.count()
        context["total_comments"] = Comment.objects.count()
        context["pending_reports"] = Report.objects.filter(is_resolved=False).count()
        context["recent_users"] = CustomUser.objects.order_by("-date_joined")[:10]
        return context


class UserManagementView(StaffRequiredMixin, ListView):
    model = CustomUser
    template_name = "dashboard/user_management.html"
    context_object_name = "users"
    paginate_by = 50
    ordering = ["-date_joined"]


class PostModerationView(StaffRequiredMixin, ListView):
    model = Post
    template_name = "dashboard/post_moderation.html"
    context_object_name = "posts"
    paginate_by = 50
    ordering = ["-created_at"]


class ReportManagementView(StaffRequiredMixin, ListView):
    model = Report
    template_name = "dashboard/report_management.html"
    context_object_name = "reports"
    paginate_by = 50
    ordering = ["-created_at"]


class ResolveReportView(StaffRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        report = get_object_or_404(Report, pk=self.kwargs["pk"])
        report.is_resolved = True
        report.resolved_by = request.user
        report.resolved_at = timezone.now()
        report.save()
        return redirect("dashboard:dashboard_reports")
