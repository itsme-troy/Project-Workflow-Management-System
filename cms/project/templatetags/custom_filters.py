from django import template
from django.utils.text import slugify

register = template.Library()

@register.filter
def dict_value(d, key):
    return d.get(key, '#ccc')

@register.filter
def format_end_date(start_date, end_date):
    # Check if the years are the same
    if start_date.year == end_date.year:
        # Return only the month, day and time for the end date if the years are the same
        return end_date.strftime("%b %d, %g %I:%M %p")  # Use %g for short year (e.g., 24)
    else:
        # Display full date for both start and end if years differ
        return end_date.strftime("%b %d, %Y, %I:%M %p")


@register.filter(name='get_item')
@register.filter
def get_item(dictionary, key):
    """Returns the value from a dictionary by key."""
    return dictionary.get(key, None)

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

# Custom filter to create a range for template loops
@register.filter
def rangefilter(value):
    """Returns a range from 1 to `value` (inclusive)."""
    try:
        value = int(value)
        return range(1, value + 1)
    except (ValueError, TypeError):
        return []
    
@register.filter
def to_range(value):
    """
    Custom filter to generate a range of numbers from 1 to the given value.
    Example: 
        {{ max_proponents|to_range }}
    """
    return range(1, value + 1)


@register.filter
def add_extra_cells(panel_count, max_panel_count):
    """
    Custom filter to calculate the number of extra cells needed to match the max panel count.
    """
    if isinstance(panel_count, int) and isinstance(max_panel_count, int):
        return max_panel_count - panel_count
    return 0