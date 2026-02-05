"""
Template tags personnalisés pour les notifications
Plateforme crowdBuilding - Burkina Faso
"""
from django import template
from django.contrib.auth.models import AnonymousUser

register = template.Library()


@register.filter
def unread_notifications_count(user):
    """
    Retourne le nombre de notifications non lues pour un utilisateur
    """
    if isinstance(user, AnonymousUser):
        return 0
    
    try:
        return user.notifications.filter(lue=False).count()
    except:
        return 0


@register.filter
def recent_notifications(user, limit=5):
    """
    Retourne les notifications récentes d'un utilisateur
    """
    if isinstance(user, AnonymousUser):
        return []
    
    try:
        return user.notifications.all()[:limit]
    except:
        return []


# AJOUTEZ CES NOUVELLES FONCTIONS :

@register.filter
def filter_by_type(notifications, types_str):
    """
    Filtre les notifications par type
    Usage dans template: {{ notifications|filter_by_type:"TYPE1,TYPE2" }}
    """
    if not notifications:
        return []
    
    try:
        types = [t.strip() for t in types_str.split(',')]
        return [n for n in notifications if hasattr(n, 'type') and n.type in types]
    except (AttributeError, ValueError):
        return []


@register.filter
def get_notifications_by_user(notifications, user):
    """Filtre les notifications par utilisateur"""
    return [n for n in notifications if n.utilisateur == user]


@register.filter
def get_unread_count_by_type(notifications, notification_type):
    """Compte les notifications non lues d'un type spécifique"""
    return len([n for n in notifications if n.type == notification_type and not n.lue])