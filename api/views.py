"""DRF viewsets for the SocialNet API."""

from django.contrib.auth import get_user_model

from rest_framework import permissions, viewsets

from comments.models import Comment
from messaging.models import Conversation, Message
from posts.models import Post

from .serializers import (
    CommentSerializer,
    ConversationSerializer,
    MessageSerializer,
    PostSerializer,
    UserSerializer,
)

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Allow edit only to the author of the object."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            obj.author == request.user or getattr(obj, "sender", None) == request.user
        )


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for user profiles."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class PostViewSet(viewsets.ModelViewSet):
    """CRUD endpoint for posts."""

    queryset = Post.objects.select_related("author").prefetch_related("tags")
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if self.action == "list":
            return qs.filter(
                visibility__in=["public", "friends"],
                is_draft=False,
            ) | qs.filter(author=user)
        return qs


class CommentViewSet(viewsets.ModelViewSet):
    """CRUD endpoint for comments."""

    queryset = Comment.objects.select_related("author", "post")
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for user conversations."""

    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related("participants")


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only endpoint for conversation messages."""

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conv_id = self.request.query_params.get("conversation")
        qs = Message.objects.select_related("sender")
        if conv_id:
            qs = qs.filter(
                conversation_id=conv_id,
                conversation__participants=self.request.user,
            )
        return qs
