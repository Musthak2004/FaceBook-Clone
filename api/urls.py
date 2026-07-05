"""API URL configuration."""

from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"users", views.UserViewSet)
router.register(r"posts", views.PostViewSet)
router.register(r"comments", views.CommentViewSet)
router.register(r"conversations", views.ConversationViewSet, basename="conversation")
router.register(r"messages", views.MessageViewSet, basename="message")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),
]
