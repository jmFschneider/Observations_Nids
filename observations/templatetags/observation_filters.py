from pathlib import PurePosixPath

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


@register.filter
def basename(value):
    """
    Retourne uniquement le nom du fichier à partir d'un chemin stocké en DB (chemin_image).
    Ex: "jpeg_7-12/TRI_NOUVEAU/FUSION_CROPPED/fiche 5FINAL.jpg" -> "fiche 5FINAL.jpg"
    """
    if not value:
        return ""
    return PurePosixPath(str(value)).name
