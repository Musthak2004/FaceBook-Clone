from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    UpdateView,
    DeleteView,
    View,
)

from .forms import PostForm
from .models import Post, PostImage, SavedCollection, SavedPost, Tag


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        response = super().form_valid(form)
        # Handle image uploads
        images = self.request.FILES.getlist("images")
        for img in images:
            PostImage.objects.create(post=self.object, image=img)
        return response

    def get_success_url(self):
        return reverse_lazy("posts:post_detail", kwargs={"pk": self.object.pk})


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = self.object.comments.filter(parent=None)
        context["is_saved"] = SavedPost.objects.filter(
            user=self.request.user, post=self.object
        ).exists()
        return context


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def test_func(self):
        return self.get_object().author == self.request.user

    def form_valid(self, form):
        response = super().form_valid(form)
        images = self.request.FILES.getlist("images")
        for img in images:
            PostImage.objects.create(post=self.object, image=img)
        return response

    def get_success_url(self):
        return reverse_lazy("posts:post_detail", kwargs={"pk": self.object.pk})


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = "posts/post_confirm_delete.html"
    success_url = reverse_lazy("core:home")

    def test_func(self):
        return self.get_object().author == self.request.user


class PostSaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs["pk"])
        collection_id = request.POST.get("collection_id") or request.GET.get(
            "collection_id"
        )

        existing = SavedPost.objects.filter(user=request.user, post=post).first()
        if existing:
            existing.delete()
            return JsonResponse({"saved": False})

        collection = None
        if collection_id:
            collection = get_object_or_404(
                SavedCollection, pk=collection_id, user=request.user
            )

        SavedPost.objects.create(user=request.user, post=post, collection=collection)
        return JsonResponse({"saved": True})


class SavedPostListView(LoginRequiredMixin, ListView):
    """Show saved posts grouped by collection."""

    template_name = "posts/saved_posts.html"
    context_object_name = "saved_posts"
    paginate_by = 20

    def get_queryset(self):
        return (
            SavedPost.objects.filter(user=self.request.user)
            .select_related("post__author", "collection")
            .prefetch_related("post__images")
        )


class CollectionCreateView(LoginRequiredMixin, CreateView):
    """Create a new collection for saving posts."""

    model = SavedCollection
    fields = ["name", "description"]
    template_name = "posts/collection_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("posts:saved_posts")


class CollectionDetailView(LoginRequiredMixin, DetailView):
    """Show posts in a collection."""

    model = SavedCollection
    template_name = "posts/collection_detail.html"
    context_object_name = "collection"

    def get_queryset(self):
        return SavedCollection.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["saved_posts"] = self.object.saved_posts.select_related(
            "post__author"
        ).prefetch_related("post__images")
        return context


class CollectionDeleteView(LoginRequiredMixin, View):
    """AJAX endpoint to delete a collection."""

    def post(self, request, *args, **kwargs):
        collection = get_object_or_404(
            SavedCollection, pk=self.kwargs["pk"], user=request.user
        )
        collection.delete()
        return JsonResponse({"deleted": True})


class SharePostView(LoginRequiredMixin, View):
    """AJAX endpoint to create a repost of an existing post."""

    def post(self, request, *args, **kwargs):
        original = get_object_or_404(Post, pk=self.kwargs["pk"])
        content = request.POST.get("content", "").strip()
        visibility = request.POST.get("visibility", "public")
        post = Post.objects.create(
            author=request.user,
            content=content,
            visibility=visibility,
            shared_post=original,
        )
        return JsonResponse({"shared": True, "post_url": post.get_absolute_url()})


class HashtagDetailView(LoginRequiredMixin, ListView):
    """Show all public/friends posts tagged with a given hashtag."""

    template_name = "posts/hashtag_detail.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_queryset(self):
        slug = self.kwargs["slug"]
        return (
            Post.objects.filter(tags__name__iexact=slug, is_draft=False)
            .select_related("author")
            .prefetch_related("images", "reactions")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tag_name"] = self.kwargs["slug"]
        return context


class TrendingTagsView(LoginRequiredMixin, ListView):
    """Show trending hashtags ordered by usage count."""

    template_name = "posts/trending_tags.html"
    context_object_name = "tags"

    def get_queryset(self):
        return (
            Tag.objects.annotate(post_count=Count("posts"))
            .filter(post_count__gt=0)
            .order_by("-post_count")[:50]
        )
