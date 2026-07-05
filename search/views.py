from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.views.generic import ListView

from accounts.models import CustomUser
from posts.models import Post


class SearchResultsView(LoginRequiredMixin, ListView):
    template_name = "search/search_results.html"
    context_object_name = "results"
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get("q", "").strip()
        search_type = self.request.GET.get("type", "all")

        if not query:
            return []

        if search_type == "users":
            return self.search_users(query)
        elif search_type == "posts":
            return self.search_posts(query)
        else:
            return []  # 'all' not used since we separate results by type

    def search_users(self, query):
        return CustomUser.objects.filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(bio__icontains=query)
        )

    def search_posts(self, query):
        return (
            Post.objects.filter(Q(content__icontains=query) & Q(is_draft=False))
            .filter(Q(visibility="public") | Q(author=self.request.user))
            .distinct()
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "").strip()
        context["query"] = query
        context["search_type"] = self.request.GET.get("type", "all")
        if query:
            context["user_results"] = self.search_users(query)[:10]
            context["post_results"] = self.search_posts(query)[:10]
        return context
