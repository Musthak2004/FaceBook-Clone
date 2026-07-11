"""
Story views: list (friends' active stories), create, detail (auto-advance).
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView

from .models import Story
from .forms import StoryForm


class StoryListView(LoginRequiredMixin, ListView):
    """Show active stories from friends."""

    model = Story
    template_name = "stories/story_list.html"
    context_object_name = "stories"

    def get_queryset(self):
        from friendships.models import Friendship

        friend_ids = Friendship.objects.filter(
            from_user=self.request.user,
            status="accepted",
        ).values_list("to_user_id", flat=True)

        return Story.active_stories.filter(
            user_id__in=list(friend_ids) + [self.request.user.id],
        ).select_related("user").order_by("user__username", "-created_at")


class StoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new story."""

    model = Story
    form_class = StoryForm
    template_name = "stories/story_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("stories:detail", kwargs={"pk": self.object.pk})


class StoryDetailView(LoginRequiredMixin, DetailView):
    """View a story with auto-advance to the next story by the same user."""

    model = Story
    template_name = "stories/story_detail.html"
    context_object_name = "story"

    def get_queryset(self):
        return Story.active_stories.select_related("user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        story = self.get_object()

        # Get all active stories for this user
        user_stories = list(
            Story.active_stories
            .filter(user=story.user)
            .order_by("created_at")
        )

        context["user_stories"] = user_stories
        context["story_index"] = next(
            (i for i, s in enumerate(user_stories) if s.pk == story.pk),
            0,
        )
        context["total_stories"] = len(user_stories)

        # Next story for auto-advance (or None if last)
        idx = context["story_index"]
        context["next_story"] = (
            user_stories[idx + 1] if idx + 1 < len(user_stories) else None
        )
        return context
