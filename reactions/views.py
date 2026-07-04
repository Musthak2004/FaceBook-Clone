from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from posts.models import Post
from .models import Reaction


class PostLikeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        reaction_type = request.POST.get('reaction_type', 'like')

        reaction, created = Reaction.objects.get_or_create(
            user=request.user,
            post=post,
            defaults={'reaction_type': reaction_type}
        )

        if not created:
            if reaction.reaction_type == reaction_type:
                reaction.delete()
                return JsonResponse({
                    'liked': False,
                    'total_likes': post.reactions.count(),
                })
            else:
                reaction.reaction_type = reaction_type
                reaction.save()

        return JsonResponse({
            'liked': True,
            'total_likes': post.reactions.count(),
            'reaction_type': reaction_type,
        })
