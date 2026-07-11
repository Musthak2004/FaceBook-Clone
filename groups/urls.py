"""
URL patterns for groups app.
Namespace: groups
"""
from django.urls import path
from .views import (
    GroupListView,
    GroupDetailView,
    GroupCreateView,
    GroupJoinView,
)

app_name = "groups"

urlpatterns = [
    path("", GroupListView.as_view(), name="list"),
    path("new/", GroupCreateView.as_view(), name="create"),
    path("<int:pk>/", GroupDetailView.as_view(), name="detail"),
    path("<int:pk>/join/", GroupJoinView.as_view(), name="join"),
]
