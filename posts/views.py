"""
Post views: list, detail, create, update, delete, like/unlike.
Follows Django for Beginners Ch 5-6, 13-15 patterns.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from .forms import PostForm, CommentForm
from .models import Post, Like, Comment


class PostListView(LoginRequiredMixin, ListView):
    """Display all posts from user and friends (news feed). Follows Ch 5 ListView pattern."""
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        from friendships.models import Friendship

        # Get friends' IDs
        friend_ids = Friendship.objects.filter(
            from_user=self.request.user,
            status="accepted",
        ).values_list("to_user_id", flat=True)

        # Include own posts and friends' posts
        user_ids = list(friend_ids) + [self.request.user.id]
        return Post.objects.filter(
            author_id__in=user_ids, group__isnull=True,
        ).select_related("author").prefetch_related(
            "likes", "comments", "images"
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["post_form"] = PostForm()
        # Mark which posts the current user has liked
        user_likes = Like.objects.filter(
            user=self.request.user,
            post_id__in=[p.id for p in context["posts"]],
        ).values_list("post_id", flat=True)
        context["user_likes"] = set(user_likes)
        return context


class PostDetailView(LoginRequiredMixin, DetailView):
    """Individual post detail. Follows Ch 5 DetailView pattern."""
    model = Post
    template_name = "posts/post_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comment_form"] = CommentForm()
        context["user_liked"] = Like.objects.filter(
            user=self.request.user,
            post=self.get_object(),
        ).exists()
        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    """Create a new post. Follows Ch 6/14 CreateView with auto-author pattern."""
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        # Handle optional group FK from POST data
        group_pk = self.request.POST.get("group")
        if group_pk:
            from groups.models import Group
            try:
                form.instance.group = Group.objects.get(pk=group_pk)
            except Group.DoesNotExist:
                pass
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.META.get("HTTP_REFERER", "/")


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit a post. Follows Ch 6/14 UpdateView permission pattern."""
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a post. Follows Ch 6/14 DeleteView permission pattern."""
    model = Post
    template_name = "posts/post_confirm_delete.html"
    success_url = reverse_lazy("home")

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user


class PostFeedAPIView(LoginRequiredMixin, View):
    """AJAX JSON endpoint for load-more posts. GET /api/posts/?offset=N"""

    BATCH_SIZE = 10

    def get(self, request, *args, **kwargs):
        try:
            offset = int(request.GET.get("offset", 0))
        except (ValueError, TypeError):
            return HttpResponseBadRequest("Invalid offset parameter")
        if offset < 0:
            return HttpResponseBadRequest("Offset cannot be negative")

        from friendships.models import Friendship

        friend_ids = Friendship.objects.filter(
            from_user=request.user,
            status="accepted",
        ).values_list("to_user_id", flat=True)
        user_ids = list(friend_ids) + [request.user.id]

        posts = Post.objects.filter(
            author_id__in=user_ids, group__isnull=True,
        ).select_related("author").prefetch_related(
            "comments", "images"
        ).annotate(
            _like_count=Count("likes"),
            _comment_count=Count("comments"),
        ).order_by("-created_at")[offset:offset + self.BATCH_SIZE + 1]

        has_more = len(posts) > self.BATCH_SIZE
        posts = list(posts[:self.BATCH_SIZE])

        # Mark which posts the current user liked
        user_likes = set(Like.objects.filter(
            user=request.user,
            post_id__in=[p.id for p in posts],
        ).values_list("post_id", flat=True))

        from django.template.loader import render_to_string
        html_parts = []
        for post in posts:
            html_parts.append(render_to_string("includes/post_card.html", {
                "post": post,
                "user": request.user,
                "user_likes": user_likes,
                "show_comment_preview": True,
            }, request=request))

        from django.http import JsonResponse
        return JsonResponse({
            "html": "".join(html_parts),
            "next_offset": offset + len(posts),
            "has_more": has_more,
        })


class LikeToggleView(LoginRequiredMixin, View):
    """AJAX-friendly like/unlike toggle."""

    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs["pk"])
        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post,
        )
        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "liked": liked,
                "like_count": post.likes.count(),
            })
        return redirect(post.get_absolute_url())


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Add a comment to a post. Follows Ch 15 comment pattern."""
    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(Post, pk=self.kwargs["post_pk"])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "post_detail",
            kwargs={"pk": self.kwargs["post_pk"]},
        )


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a comment. Only the comment author can delete."""
    model = Comment

    def test_func(self):
        obj = self.get_object()
        return obj.author == self.request.user

    def get_success_url(self):
        return reverse_lazy("post_detail", kwargs={"pk": self.object.post.pk})
