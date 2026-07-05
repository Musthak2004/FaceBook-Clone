from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView

from accounts.models import CustomUser
from friendships.models import Friendship
from posts.models import Post
from stories.models import Story


class HomeFeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = "core/home.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        friend_ids = Friendship.get_friends(user)
        return (
            Post.objects.filter(
                Q(author=user)
                | Q(author__id__in=friend_ids, visibility__in=["public", "friends"])
                | Q(visibility="public")
            )
            .filter(is_draft=False)
            .select_related("author")
            .prefetch_related("images", "reactions", "comments")
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        friend_ids = Friendship.get_friends(user)
        context["friend_suggestions"] = CustomUser.objects.exclude(
            id__in=friend_ids
        ).exclude(id=user.id)[:5]
        context["stories_grouped"] = Story.stories_grouped_by_user()
        return context
