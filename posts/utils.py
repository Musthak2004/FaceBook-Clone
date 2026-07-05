"""Content parsing utilities for hashtags (#tag) and mentions (@username)."""

import re

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

HASHTAG_RE = re.compile(r"#(\w+)")
MENTION_RE = re.compile(r"@(\w+)")

User = get_user_model()


def parse_hashtags(content):
    """Return a set of unique, lowercased hashtag strings found in content."""
    if not content:
        return set()
    return {m.lower() for m in HASHTAG_RE.findall(content)}


def parse_mentions(content):
    """Return a set of unique username strings found in content (case-preserved)."""
    if not content:
        return set()
    return set(MENTION_RE.findall(content))


def render_content(content):
    """Render post/comment content with clickable hashtags and @mentions.

    Steps:
        1. HTML-escape the content to prevent XSS.
        2. Replace ``#hashtag`` with an ``<a>`` linking to the tag detail page.
        3. Replace ``@username`` with an ``<a>`` linking to the user's profile
           (only if the username exists in the database).
        4. Return the result wrapped in ``mark_safe()``.
    """
    if not content:
        return ""

    escaped = escape(content)

    # Replace #hashtags with links to the tag detail page
    def _replace_hashtag(match):
        tag = match.group(1).lower()
        url = reverse("posts:hashtag_detail", kwargs={"slug": tag})
        return f'<a href="{url}" class="hashtag">#{tag}</a>'

    # Replace @mentions with links to user profiles (only for existing users)
    def _replace_mention(match):
        username = match.group(1)
        if User.objects.filter(username__iexact=username).exists():
            url = reverse("accounts:profile", kwargs={"username": username})
            return f'<a href="{url}" class="mention">@{username}</a>'
        return f"@{username}"

    result = HASHTAG_RE.sub(_replace_hashtag, escaped)
    result = MENTION_RE.sub(_replace_mention, result)
    return mark_safe(result)
