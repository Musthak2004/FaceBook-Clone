"""
Custom template tags for the messaging app.
"""
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Template filter to access a dict value by key: ``mydict|get_item:key``."""
    return dictionary.get(key, 0)
