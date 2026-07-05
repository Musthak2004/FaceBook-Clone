"""URL configuration for the Groups app."""

from django.urls import path

from . import views

app_name = "groups"

urlpatterns = [
    path("", views.GroupListView.as_view(), name="group_list"),
    path("create/", views.GroupCreateView.as_view(), name="group_create"),
    path("<int:pk>/", views.GroupDetailView.as_view(), name="group_detail"),
    path("<int:pk>/toggle/", views.GroupJoinLeaveView.as_view(), name="group_toggle"),
    path("<int:pk>/post/", views.GroupPostCreateView.as_view(), name="group_post"),
]
