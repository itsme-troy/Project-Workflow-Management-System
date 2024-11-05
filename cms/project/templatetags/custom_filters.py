from django import template
from django.utils.text import slugify

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def subtract(value, arg):
    """Subtracts arg from value."""
    try:
        value = int(value)
        arg = int(arg)
        return value - arg
    except (ValueError, TypeError):
        return value

@register.filter
def range_filter(value):
    """Returns a range object."""
    try:
        return range(int(value))
    except (ValueError, TypeError):
        return []
    
@register.filter
def slugify_filter(value):
    return slugify(value)