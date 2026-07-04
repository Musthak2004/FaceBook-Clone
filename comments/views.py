from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.views.generic import DeleteView, UpdateView

from .models import Comment


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment

    def test_func(self):
        return self.get_object().author == self.request.user

    def delete(self, request, *args, **kwargs):
        comment = self.get_object()
        comment.delete()
        return JsonResponse({'deleted': True})


class CommentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Comment
    fields = ['content']

    def test_func(self):
        return self.get_object().author == self.request.user

    def form_valid(self, form):
        form.save()
        return JsonResponse({
            'edited': True,
            'content': form.instance.content,
        })
