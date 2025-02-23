from django import template
from datetime import date

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Custom template filter to get dictionary values safely."""
    return dictionary.get(key, "")

@register.filter
def is_today(value):
    """
    Check if the given date is today's date.
    """
    return value == date.today()
@register.filter
def in_group(user, group_name):
    return user.groups.filter(name=group_name).exists() if user.is_authenticated else False

@register.filter
def dict_get(dictionary, key):
    """Returns the value of a dictionary given a key, or None if the key doesn't exist."""
    return dictionary.get(key, None)
