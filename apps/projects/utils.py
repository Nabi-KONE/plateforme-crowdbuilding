# apps/projects/utils.py
from django.utils import timezone

def add_months(source_date, months):
    """Ajoute un nombre de mois à une date"""
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, [31,
        29 if year % 4 == 0 and (not year % 100 == 0 or year % 400 == 0) else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
    return timezone.datetime(year, month, day).date()

"""
Utils pour le module projects
"""
from django.db.models import Q
from apps.accounts.models import Utilisateur, TypeRole, StatutRole


def get_administrateurs():
    """
    Retourne la liste des administrateurs validés
    - Superusers et staff Django
    - Utilisateurs avec rôle ADMINISTRATEUR validé
    """
    try:
        # Récupérer les administrateurs par rôle
        administrateurs_par_role = Utilisateur.objects.filter(
            roles__type=TypeRole.ADMINISTRATEUR,
            roles__statut=StatutRole.VALIDE
        ).distinct()
        
        # Récupérer les superusers/staff
        superusers = Utilisateur.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True)
        ).distinct()
        
        # Combiner les deux querysets (éviter les doublons)
        return (administrateurs_par_role | superusers).distinct()
        
    except Exception as e:
        # Fallback sécurisé
        print(f"⚠️ Erreur get_administrateurs: {e}")
        return Utilisateur.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True)
        )


def envoyer_notification_aux_administrateurs(titre, contenu, type_notif, lien='#'):
    """
    Fonction utilitaire pour envoyer des notifications aux administrateurs
    """
    try:
        from apps.notifications.models import Notification
        
        administrateurs = get_administrateurs()
        
        notifications_creees = 0
        for admin in administrateurs:
            try:
                Notification.objects.create(
                    utilisateur=admin,
                    titre=titre,
                    contenu=contenu,
                    type=type_notif,
                    lien=lien
                )
                notifications_creees += 1
            except Exception as e:
                print(f"Erreur création notification pour {admin.email}: {e}")
        
        return notifications_creees > 0
        
    except ImportError:
        print("⚠️ Module notifications non disponible")
        return False
    except Exception as e:
        print(f"⚠️ Erreur envoi notifications: {e}")
        return False