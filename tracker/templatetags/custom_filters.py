from django import template
from django.contrib.auth.models import Group
import locale
register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()

@register.filter
def german_number(value):
    try:
        value = float(value)  # Ensure it's a float
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value  # Return original if conversion fails

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key) if dictionary else ''
