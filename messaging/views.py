from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View

from accounts.models import CustomUser
from .models import Conversation, Message


class ConversationListView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = "messaging/conversation_list.html"
    context_object_name = "conversations"

    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related("participants")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Annotate each conversation with the other participant
        conversations = context["conversations"]
        for conv in conversations:
            conv.other_participant = conv.participants.exclude(
                pk=self.request.user.pk
            ).first()
        return context


class NewConversationView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        username = self.kwargs["username"]
        other_user = get_object_or_404(CustomUser, username=username)
        if request.user == other_user:
            return redirect("messaging:conversation_list")

        # Check for existing conversation
        conversations = Conversation.objects.filter(participants=request.user).filter(
            participants=other_user
        )

        if conversations.exists():
            return redirect(
                "messaging:conversation_detail", pk=conversations.first().pk
            )

        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
        return redirect("messaging:conversation_detail", pk=conversation.pk)


class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = "messaging/conversation_detail.html"
    context_object_name = "conversation"

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()
        # Mark messages as read
        Message.objects.filter(conversation=conversation, is_read=False).exclude(
            sender=self.request.user
        ).update(is_read=True)
        # Annotate the conversation with the other participant
        conversation.other_participant = conversation.participants.exclude(
            pk=self.request.user.pk
        ).first()
        # Annotate sidebar conversations
        conversations = Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related("participants")
        for conv in conversations:
            conv.other_participant = conv.participants.exclude(
                pk=self.request.user.pk
            ).first()
        context["user_conversations"] = conversations
        return context


class SendMessageView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        conversation = get_object_or_404(
            Conversation, pk=self.kwargs["pk"], participants=request.user
        )
        content = request.POST.get("content", "").strip()
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
            )

            # Broadcast via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation.pk}",
                {
                    "type": "chat_message",
                    "id": message.pk,
                    "sender_id": request.user.id,
                    "sender_username": request.user.username,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                },
            )

            return JsonResponse(
                {
                    "sent": True,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                }
            )
        return JsonResponse({"error": "Content is required"}, status=400)
