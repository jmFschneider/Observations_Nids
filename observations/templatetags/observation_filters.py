from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def urlencode_without_page(context, **kwargs):
    query_string = context['request'].GET.copy()
    if 'page' in query_string:
        del query_string['page']
    for key, value in kwargs.items():
        query_string[key] = value
    return query_string.urlencode()
