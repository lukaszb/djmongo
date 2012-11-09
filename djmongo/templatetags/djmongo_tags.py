from django import template
from djmongo.admin import DOCUMENT_PROXY_VAR_NAME

register = template.Library()


@register.simple_tag(takes_context=True)
def get(context, item, key):
    proxy = context[DOCUMENT_PROXY_VAR_NAME] # Instance of djmongo.admin.DocumentProxy
    val = proxy.get(item, key)
    if val is None:
        return '-'
    return val

