from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
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
from .models import Post, PostImage, SavedPost


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
        saved, created = SavedPost.objects.get_or_create(user=request.user, post=post)
        if not created:
            saved.delete()
            return JsonResponse({"saved": False})
        return JsonResponse({"saved": True})


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
