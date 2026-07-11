"""
URL patterns for messaging app.
Namespace: messaging
"""
from django.urls import path
from .views import (
    ConversationListView,
    ConversationDetailView,
    ConversationCreateView,
    ConversationLeaveView,
)

app_name = "messaging"

urlpatterns = [
    path("", ConversationListView.as_view(), name="list"),
    path("new/", ConversationCreateView.as_view(), name="create"),
    path("<int:pk>/", ConversationDetailView.as_view(), name="detail"),
    path("<int:pk>/leave/", ConversationLeaveView.as_view(), name="leave"),
]
