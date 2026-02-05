# apps/admin/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def startswith(value, arg):
    """
    Vérifie si la chaîne 'value' commence par 'arg'.
    Usage dans le template: {{ request.resolver_match.url_name|startswith:"gestion_utilisateurs" }}
    """
    if not value:
        return False
    return value.startswith(arg)