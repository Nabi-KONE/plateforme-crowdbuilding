from apps.accounts.models import Utilisateur, Role, StatutRole
from apps.projects.models import Projet, CompteRendu
from apps.investments.models import Investissement
from apps.documents.models import Document


def global_stats(request):
    """
    Statistiques globales pour le sidebar admin
    Disponibles dans TOUS les templates
    """
    if not request.user.is_authenticated:
        return {}

    # Sécurité : uniquement admin
    if not request.user.est_administrateur():
        return {}

    return {
        'global_stats': {
            # Utilisateurs
            'utilisateurs_en_attente': Role.objects.filter(
                statut=StatutRole.EN_ATTENTE_VALIDATION
            ).count(),

            # Projets
            'projets_en_attente': Projet.objects.filter(
                statut='EN_ATTENTE_VALIDATION'
            ).count(),

            # Investissements
            'investissements_en_attente': Investissement.objects.filter(
                statut='EN_ATTENTE'
            ).count(),

            # Comptes rendus (🔥 CORRECTION ICI)
            'comptes_rendus_en_attente': CompteRendu.objects.filter(
                statut='EN_ATTENTE_VALIDATION'
            ).count(),

            # Documents
            'documents_en_attente': Document.objects.filter(
                statut='EN_ATTENTE'
            ).count(),
        }
    }
