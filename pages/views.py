from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from .forms import PageForm
from .models import Page, PageFollower, PagePost


class PageListView(LoginRequiredMixin, ListView):
    """List all pages — public directory."""

    model = Page
    template_name = "pages/page_list.html"
    context_object_name = "pages"
    paginate_by = 20


class PageCreateView(LoginRequiredMixin, CreateView):
    """Create a new page (creator becomes admin)."""

    model = Page
    form_class = PageForm
    template_name = "pages/page_form.html"
    success_url = reverse_lazy("pages:list")

    def form_valid(self, form):
        form.instance.admin = self.request.user
        return super().form_valid(form)


class PageUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a page (admin only)."""

    model = Page
    form_class = PageForm
    template_name = "pages/page_form.html"

    def dispatch(self, request, *args, **kwargs):
        page = self.get_object()
        if page.admin != request.user:
            return JsonResponse({"error": "Only the page admin can edit."}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("pages:detail", kwargs={"pk": self.object.pk})


class PageDetailView(LoginRequiredMixin, DetailView):
    """Show a page and its posts."""

    model = Page
    template_name = "pages/page_detail.html"
    context_object_name = "page"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.get_object()
        context["posts"] = page.posts.select_related("author").all()
        context["is_following"] = page.followers.filter(user=self.request.user).exists()
        context["is_admin"] = page.admin == self.request.user
        return context


class PageFollowView(LoginRequiredMixin, View):
    """AJAX endpoint to follow or unfollow a page."""

    def post(self, request, *args, **kwargs):
        page = get_object_or_404(Page, pk=self.kwargs["pk"])

        if page.admin == request.user:
            return JsonResponse(
                {"error": "You are the admin of this page."}, status=400
            )

        follow = PageFollower.objects.filter(user=request.user, page=page)

        if follow.exists():
            follow.delete()
            return JsonResponse(
                {"is_following": False, "follower_count": page.follower_count}
            )
        else:
            PageFollower.objects.create(user=request.user, page=page)
            return JsonResponse(
                {"is_following": True, "follower_count": page.follower_count}
            )


class PagePostCreateView(LoginRequiredMixin, View):
    """AJAX endpoint to create a post on a page (admin only)."""

    def post(self, request, *args, **kwargs):
        page = get_object_or_404(Page, pk=self.kwargs["pk"])

        if page.admin != request.user:
            return JsonResponse({"error": "Only the page admin can post."}, status=403)

        content = request.POST.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "Content is required."}, status=400)

        post = PagePost.objects.create(page=page, author=request.user, content=content)
        return JsonResponse(
            {
                "created": True,
                "post_id": post.pk,
                "author": post.author.username,
                "content": post.content,
                "created_at": post.created_at.isoformat(),
            }
        )
