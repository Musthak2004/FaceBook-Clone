from django.urls import path
from . import views

app_name = 'friendships'

urlpatterns = [
    path('', views.FriendListView.as_view(), name='friend_list'),
    path('requests/', views.FriendRequestsView.as_view(), name='friend_requests'),
    path('sent/', views.SentRequestsView.as_view(), name='sent_requests'),
    path('suggestions/', views.FriendSuggestionsView.as_view(), name='friend_suggestions'),
    path('request/<int:user_id>/', views.FriendRequestView.as_view(), name='send_request'),
    path('accept/<int:request_id>/', views.AcceptFriendRequestView.as_view(), name='accept'),
    path('reject/<int:request_id>/', views.RejectFriendRequestView.as_view(), name='reject'),
    path('cancel/<int:request_id>/', views.CancelFriendRequestView.as_view(), name='cancel'),
    path('unfriend/<int:user_id>/', views.UnfriendView.as_view(), name='unfriend'),
]
