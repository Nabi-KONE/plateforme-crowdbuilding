# investissements/templatetags/investissement_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    return dictionary.get(key) if dictionary else None

@register.filter
def multiply(value, arg):
    """Multiplie value par arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divise value par arg"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_parts_for_project(investissements_par_projet, project_id):
    """Récupère les parts pour un projet spécifique"""
    projet_data = investissements_par_projet.get(project_id, {})
    return projet_data.get('parts', 0)