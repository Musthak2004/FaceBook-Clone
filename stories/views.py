from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .models import Story


class StoriesRowView(LoginRequiredMixin, TemplateView):
    """Render the stories row HTML fragment."""

    template_name = "stories/stories_row.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stories_grouped"] = Story.stories_grouped_by_user()
        return context


class StoryUploadView(LoginRequiredMixin, View):
    """AJAX endpoint to upload a new story."""

    def post(self, request):
        image = request.FILES.get("image")
        caption = request.POST.get("caption", "")

        if not image:
            return JsonResponse({"error": "No image provided."}, status=400)

        story = Story.objects.create(
            user=request.user,
            image=image,
            caption=caption,
            expires_at=timezone.now() + timezone.timedelta(hours=24),
        )
        return JsonResponse(
            {
                "id": story.pk,
                "image_url": story.image.url,
                "caption": story.caption,
                "created_at": story.created_at.isoformat(),
            }
        )


class StoryListView(LoginRequiredMixin, View):
    """AJAX endpoint to get all active stories grouped by user."""

    def get(self, request):
        grouped = Story.stories_grouped_by_user()
        data = []
        for user, stories in grouped.items():
            user_data = {
                "user_id": user.pk,
                "username": user.username,
                "profile_picture": (
                    user.profile_picture.url if user.profile_picture else None
                ),
                "stories": [
                    {
                        "id": s.pk,
                        "image_url": s.image.url,
                        "caption": s.caption,
                        "created_at": s.created_at.isoformat(),
                    }
                    for s in stories
                ],
            }
            data.append(user_data)
        return JsonResponse({"stories": data})
