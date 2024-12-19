from django import template
from django.utils.text import slugify

register = template.Library()

@register.filter(name='get_item')
@register.filter
def get_item(dictionary, key):
    """Returns the value from a dictionary by key."""
    return dictionary.get(key, None)
