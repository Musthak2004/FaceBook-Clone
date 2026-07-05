import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.views import View

from .models import Report


class ReportCreateView(LoginRequiredMixin, View):
    """AJAX endpoint to submit a report."""

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        content_type_id = data.get("content_type_id")
        object_id = data.get("object_id")
        reason = data.get("reason")
        description = data.get("description", "")

        # Support app_label + model_name as alternative to content_type_id
        if not content_type_id and data.get("model"):
            try:
                app_label, model_name = data["model"].split(".", 1)
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
                content_type_id = ct.id
            except (ValueError, ContentType.DoesNotExist):
                return JsonResponse({"error": "Invalid content type."}, status=400)

        if not all([content_type_id, object_id, reason]):
            return JsonResponse({"error": "Missing required fields."}, status=400)

        if reason not in dict(Report.REASON_CHOICES):
            return JsonResponse({"error": "Invalid reason."}, status=400)

        Report.objects.create(
            reporter=request.user,
            content_type_id=content_type_id,
            object_id=object_id,
            reason=reason,
            description=description,
        )
        return JsonResponse({"success": True})
