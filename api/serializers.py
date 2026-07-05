"""DRF serializers for the SocialNet API."""

from django.contrib.auth import get_user_model

from rest_framework import serializers

from comments.models import Comment
from messaging.models import Conversation, Message
from posts.models import Post

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile_picture",
            "bio",
            "education",
            "work",
            "location",
            "date_joined",
        ]
        read_only_fields = ["date_joined"]


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    total_likes = serializers.IntegerField(read_only=True)
    total_comments = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "content",
            "visibility",
            "is_draft",
            "shared_post",
            "tags",
            "created_at",
            "updated_at",
            "total_likes",
            "total_comments",
        ]
        read_only_fields = ["created_at", "updated_at"]


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            "id",
            "author",
            "post",
            "parent",
            "content",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "content",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "participants",
            "last_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_last_message(self, obj):
        message = obj.last_message
        if message:
            return MessageSerializer(message).data
        return None
