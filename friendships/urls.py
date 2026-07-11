"""
Friendship URL patterns.
"""
from django.urls import path
from .views import (
    FriendListView,
    FriendRequestsView,
    FriendSuggestionsView,
    SentRequestsView,
    FriendRequestView,
    FriendAcceptView,
    FriendRejectView,
    FriendRemoveView,
)

urlpatterns = [
    path("", FriendListView.as_view(), name="friend_list"),
    path("requests/", FriendRequestsView.as_view(), name="friend_requests"),
    path("sent/", SentRequestsView.as_view(), name="sent_requests"),
    path("suggestions/", FriendSuggestionsView.as_view(), name="friend_suggestions"),
    path("request/<username>/", FriendRequestView.as_view(), name="friend_request"),
    path("accept/<int:pk>/", FriendAcceptView.as_view(), name="friend_accept"),
    path("reject/<int:pk>/", FriendRejectView.as_view(), name="friend_reject"),
    path("remove/<username>/", FriendRemoveView.as_view(), name="friend_remove"),
]
