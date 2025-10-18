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
