from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import UpdateView

from .models import Comment


class CommentDeleteView(LoginRequiredMixin, View):
    """Delete a comment via AJAX POST."""

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(Comment, pk=self.kwargs["pk"])
        if comment.author != request.user:
            return JsonResponse({"error": "Forbidden"}, status=403)
        comment.delete()
        return JsonResponse({"deleted": True})


class CommentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    fields = ["content"]

    def test_func(self):
        return self.get_object().author == self.request.user

    def form_valid(self, form):
        form.save()
        return JsonResponse(
            {
                "edited": True,
                "content": form.instance.content,
            }
        )
