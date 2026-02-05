# projects/templatetags/math_filters.py
from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplie la valeur par l'argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Divise la valeur par l'argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def add(value, arg):
    """Additionne la valeur et l'argument"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return value