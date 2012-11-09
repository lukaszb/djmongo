from django import template

register = template.Library()


@register.simple_tag
def get(data, key):
    val = data.get(key)
    if val is None:
        return '-'
    return val

