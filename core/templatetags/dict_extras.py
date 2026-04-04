# core/templatetags/dict_extras.py
# এই ফাইলটা তৈরি করো: core/templatetags/__init__.py (empty) এবং এই ফাইল

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, ('', ''))