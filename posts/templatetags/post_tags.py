"""Template filters for rendering post content with hashtags and mentions."""

from django import template

from ..utils import render_content

register = template.Library()


@register.filter(is_safe=True)
def post_render(content):
    """Render post/comment text with clickable #hashtags and @mentions."""
    return render_content(content)
