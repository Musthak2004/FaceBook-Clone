"""
Management command to delete expired stories from DB and disk.

Usage: python manage.py cleanup_stories

Django's QuerySet.delete() does NOT fire post_delete signals, so we must
iterate individual instances to trigger signal-based file cleanup.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from stories.models import Story


class Command(BaseCommand):
    help = "Delete expired stories and their image files from disk."

    def handle(self, *args, **options):
        expired = Story.objects.filter(expires_at__lt=timezone.now())
        count = expired.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No expired stories found."))
            return

        # Delete one-by-one to trigger post_delete signals (file cleanup)
        for story in expired:
            story.delete()

        self.stdout.write(
            self.style.SUCCESS(f"Deleted {count} expired stories.")
        )
