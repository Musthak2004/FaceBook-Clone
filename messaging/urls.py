from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path("", views.ConversationListView.as_view(), name="conversation_list"),
    path(
        "new/<str:username>/",
        views.NewConversationView.as_view(),
        name="new_conversation",
    ),
    path(
        "<int:pk>/", views.ConversationDetailView.as_view(), name="conversation_detail"
    ),
    path("<int:pk>/send/", views.SendMessageView.as_view(), name="send_message"),
]
