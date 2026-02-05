from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Soustrait arg à value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divisibleby(value, arg):
    """Divise value par arg"""
    try:
        return int(value) / int(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0