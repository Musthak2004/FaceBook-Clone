"""
Static page views.
Follows Django for Beginners Ch 10 TemplateView pattern.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from posts.models import Post, Like
from posts.forms import PostForm


class HomePageView(LoginRequiredMixin, TemplateView):
    """Home page showing the news feed."""
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from friendships.models import Friendship

        # Get news feed posts (own + friends')
        friend_ids = Friendship.objects.filter(
            from_user=self.request.user,
            status="accepted",
        ).values_list("to_user_id", flat=True)
        user_ids = list(friend_ids) + [self.request.user.id]

        posts = Post.objects.filter(
            author_id__in=user_ids, group__isnull=True,
        ).select_related("author").prefetch_related(
            "likes", "comments", "images"
        ).order_by("-created_at")[:20]

        context["posts"] = posts
        context["post_form"] = PostForm()

        # Which posts the current user liked
        user_likes = Like.objects.filter(
            user=self.request.user,
            post_id__in=[p.id for p in posts],
        ).values_list("post_id", flat=True)
        context["user_likes"] = set(user_likes)

        # Friend suggestions
        User = self.request.user.__class__
        friend_ids_set = set(self.request.user.friends.values_list("id", flat=True))
        sent_ids = set(self.request.user.friendship_requests_sent.values_list(
            "to_user_id", flat=True
        ))
        exclude = friend_ids_set | sent_ids | {self.request.user.id}
        context["suggestions"] = User.objects.exclude(id__in=exclude)[:5]

        return context
