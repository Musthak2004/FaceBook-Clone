"""
Messaging views: conversation list, detail (chat), create, and leave.
Uses Django for Beginners patterns (LoginRequiredMixin, ListView, DetailView).
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, View

from .models import Conversation, Message, MessageReadReceipt
from .forms import MessageForm, ConversationCreateForm


class ConversationListView(LoginRequiredMixin, ListView):
    """List the current user's conversations, ordered by most recent message."""

    model = Conversation
    template_name = "messaging/conversation_list.html"
    context_object_name = "conversations"

    def get_queryset(self):
        base_qs = Conversation.objects.filter(
            participants=self.request.user,
        ).prefetch_related("participants")

        # Annotate with last_message_created for ordering
        last_msg = Message.objects.filter(
            conversation=OuterRef("pk"),
        ).order_by("-created_at")
        return base_qs.annotate(
            last_msg_time=Subquery(last_msg.values("created_at")[:1]),
        ).order_by("-last_msg_time", "-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        unread_counts = {}
        total_unread = 0
        for conv in context["conversations"]:
            count = Message.objects.filter(
                conversation=conv,
            ).exclude(
                sender=self.request.user,
            ).exclude(
                pk__in=MessageReadReceipt.objects.filter(
                    user=self.request.user,
                    message__conversation=conv,
                ).values("message_id"),
            ).count()
            unread_counts[conv.pk] = count
            total_unread += count
        context["unread_counts"] = unread_counts
        context["total_unread"] = total_unread
        return context


class ConversationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View a single conversation's message history and send messages."""

    model = Conversation
    template_name = "messaging/conversation_detail.html"
    paginate_by = 50

    def test_func(self):
        conv = self.get_object()
        return self.request.user in conv.participants.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()

        # Mark unread messages as read
        self._mark_as_read(conversation)

        messages = conversation.messages.select_related("sender")
        context["messages"] = messages.order_by("-created_at")
        context["form"] = MessageForm()
        context["participants"] = conversation.participants.all()

        # Read receipts grouped by message
        read_receipts = MessageReadReceipt.objects.filter(
            message__conversation=conversation,
        ).select_related("user")
        receipts_by_msg = {}
        for rr in read_receipts:
            receipts_by_msg.setdefault(rr.message_id, []).append(rr.user.username)
        context["read_receipts"] = receipts_by_msg

        return context

    def _mark_as_read(self, conversation):
        """Create read receipts for all unread messages by this user."""
        unread_msgs = Message.objects.filter(
            conversation=conversation,
        ).exclude(
            sender=self.request.user,
        ).exclude(
            pk__in=MessageReadReceipt.objects.filter(
                user=self.request.user,
            ).values("message_id"),
        )
        receipts = [
            MessageReadReceipt(message=msg, user=self.request.user)
            for msg in unread_msgs
        ]
        MessageReadReceipt.objects.bulk_create(receipts, ignore_conflicts=True)

    def post(self, request, *args, **kwargs):
        conversation = self.get_object()
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
        return redirect(
            reverse_lazy("messaging:detail", kwargs={"pk": conversation.pk}),
        )


class ConversationCreateView(LoginRequiredMixin, CreateView):
    """Create a new conversation with selected participants."""

    model = Conversation
    form_class = ConversationCreateForm
    template_name = "messaging/conversation_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        # Add the current user as a participant
        self.object.participants.add(self.request.user)
        return response

    def get_success_url(self):
        return reverse_lazy("messaging:detail", kwargs={"pk": self.object.pk})


class ConversationLeaveView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Remove the current user from a conversation's participants."""

    def test_func(self):
        conv = get_object_or_404(Conversation, pk=self.kwargs["pk"])
        return self.request.user in conv.participants.all()

    def post(self, request, *args, **kwargs):
        conv = get_object_or_404(Conversation, pk=kwargs["pk"])
        conv.participants.remove(request.user)
        return redirect(reverse_lazy("messaging:list"))
