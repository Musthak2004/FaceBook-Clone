from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView

from friendships.models import Friendship
from posts.models import PollVote, Post
from stories.models import Story


class HomeFeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "core/home.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        friend_ids = Friendship.get_friends(user)

        # Exclude blocked users and users who blocked the current user
        blocked_ids = Friendship.objects.filter(
            Q(from_user=user, status="blocked") | Q(to_user=user, status="blocked")
        ).values_list("from_user", "to_user")

        blocked_users = set()
        for f, t in blocked_ids:
            blocked_users.add(f)
            blocked_users.add(t)
        blocked_users.discard(user.id)

        return (
            Post.objects.filter(
                Q(author=user)
                | Q(author__id__in=friend_ids, visibility__in=["public", "friends"])
                | Q(visibility="public")
            )
            .exclude(author__id__in=blocked_users)
            .filter(is_draft=False)
            .select_related("author")
            .prefetch_related(
                "images", "reactions", "comments", "poll", "poll__options"
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context["friend_suggestions"] = Friendship.get_suggestions(user, limit=5)
        context["stories_grouped"] = Story.stories_grouped_by_user()

        # Collect which posts the user has voted on
        post_ids = [p.id for p in context["posts"]]
        voted_poll_ids = set(
            PollVote.objects.filter(
                user=user, option__poll__post_id__in=post_ids
            ).values_list("option__poll_id", flat=True)
        )
        context["voted_poll_ids"] = voted_poll_ids
        return context
