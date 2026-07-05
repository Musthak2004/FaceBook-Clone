from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="dashboard_home"),
    path("users/", views.UserManagementView.as_view(), name="dashboard_users"),
    path("posts/", views.PostModerationView.as_view(), name="dashboard_posts"),
    path("reports/", views.ReportManagementView.as_view(), name="dashboard_reports"),
    path(
        "reports/resolve/<int:pk>/",
        views.ResolveReportView.as_view(),
        name="resolve_report",
    ),
]
