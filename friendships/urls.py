from django.urls import path

from . import views

app_name = "friendships"

urlpatterns = [
    path("requests/", views.FriendRequestListView.as_view(), name="friend_requests"),
    path(
        "requests/send/<int:pk>/", views.SendRequestView.as_view(), name="send_request"
    ),
    path(
        "requests/accept/<int:pk>/",
        views.AcceptRequestView.as_view(),
        name="accept_request",
    ),
    path(
        "requests/reject/<int:pk>/",
        views.RejectRequestView.as_view(),
        name="reject_request",
    ),
    path("remove/<int:pk>/", views.RemoveFriendView.as_view(), name="remove_friend"),
    path("block/<int:pk>/", views.BlockUserView.as_view(), name="block_user"),
    path("unblock/<int:pk>/", views.UnblockUserView.as_view(), name="unblock_user"),
]
