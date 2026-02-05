from django import template

register = template.Library()

@register.filter
def filter_by_type(notifications, types_str):
    """
    Filtre les notifications par type
    Usage dans le template : {{ notifications|filter_by_type:"TYPE1,TYPE2" }}
    """
    if not notifications:
        return []
    
    types = [t.strip() for t in types_str.split(',')]
    return [n for n in notifications if n.type in types]

@register.filter
def get_notifications_by_user(notifications, user):
    """Filtre les notifications par utilisateur"""
    return [n for n in notifications if n.utilisateur == user]

@register.filter
def get_unread_count_by_type(notifications, notification_type):
    """Compte les notifications non lues d'un type spécifique"""
    return len([n for n in notifications if n.type == notification_type and not n.lue])

@register.filter
def sort_by_date(notifications, order='desc'):
    """Trie les notifications par date"""
    if order == 'asc':
        return sorted(notifications, key=lambda x: x.date_creation)
    else:
        return sorted(notifications, key=lambda x: x.date_creation, reverse=True)