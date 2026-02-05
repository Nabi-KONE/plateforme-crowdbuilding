"""
Vues principales pour la plateforme crowdBuilding
Plateforme de Financement Participatif dans l'Immobilier - Burkina Faso
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from apps.projects.models import Projet
from apps.investments.models import Investissement
from apps.notifications.models import Notification
from apps.accounts.models import Utilisateur


def home(request):
    """
    Page d'accueil de la plateforme
    """
    # Statistiques générales
    stats = {
        'total_projets': Projet.objects.filter(
            statut__in=['VALIDE', 'EN_COURS_FINANCEMENT', 'FINANCE', 'EN_REALISATION', 'TERMINE']
        ).count(),
        'projets_actifs': Projet.objects.filter(
            statut__in=['VALIDE', 'EN_COURS_FINANCEMENT']
        ).count(),
        'montant_total_collecte': Investissement.objects.filter(
            statut='CONFIRME'
        ).aggregate(total=Sum('montant'))['total'] or 0,
        'total_investisseurs': Investissement.objects.filter(
            statut='CONFIRME'
        ).values('investisseur').distinct().count(),
    }
    
    # Projets en vedette (les plus récents validés)
    projets_vedette = Projet.objects.filter(
        statut__in=['VALIDE', 'EN_COURS_FINANCEMENT']
    ).order_by('-date_creation')[:6]
    
    # Projets les plus financés
    projets_populaires = Projet.objects.filter(
        statut__in=['VALIDE', 'EN_COURS_FINANCEMENT', 'FINANCE']
    ).annotate(
        total_investissements=Count('investissements', filter=Q(investissements__statut='CONFIRME'))
    ).order_by('-total_investissements')[:3]
    
    context = {
        'stats': stats,
        'projets_vedette': projets_vedette,
        'projets_populaires': projets_populaires,
    }
    
    return render(request, 'core/home.html', context)


@login_required
def dashboard(request):
    """
    Tableau de bord central - REDIRECTION VERS LE BON DASHBOARD
    """
    user = request.user
    
    # 1. Vérifier le statut du rôle actif (en attente de validation)
    role_actif = user.get_role_actif()
    if role_actif and role_actif.statut == 'EN_ATTENTE_VALIDATION':
        # Utilisateur en attente de validation
        return render(request, 'accounts/dashboard_attente.html', get_dashboard_attente_data(user))
    
    # 2. Rediriger selon le rôle validé
    if user.est_administrateur():
        # Si vous avez un dashboard admin spécifique
        return redirect('admin_perso:dashboard')
        # OU si vous avez un template admin/dashboard_admin.html
        # return render(request, 'admin/dashboard_admin.html', get_dashboard_admin_data())
    
    elif user.est_promoteur():
        # REDIRECTION VERS LE DASHBOARD PROMOTEUR
        return redirect('projects:promoteur_dashboard') 
    
    elif user.est_investisseur():
        # REDIRECTION VERS LE DASHBOARD INVESTISSEUR
        return redirect('investments:dashboard_investisseur')
    
    else:
        # Cas par défaut (aucun rôle)
        messages.info(request, "Veuillez sélectionner un rôle pour accéder au tableau de bord.")
        return redirect('accounts:switch_role')

def get_dashboard_admin_data():
    """
    Données pour le dashboard administrateur
    """
    from django.db.models import Q, Sum, Count
    from apps.documents.models import Document

    # Stats générales
    total_projets = Projet.objects.count()
    projets_finances = Projet.objects.filter(statut='FINANCE').count()

    stats = {
        'total_utilisateurs': Utilisateur.objects.count(),
        'utilisateurs_en_attente': Utilisateur.objects.filter(
            roles__statut='EN_ATTENTE_VALIDATION'
        ).distinct().count(),
        'total_projets': total_projets,
        'projets_en_attente': Projet.objects.filter(
            statut='EN_ATTENTE_VALIDATION'
        ).count(),
        'total_investissements': Investissement.objects.filter(
            statut='CONFIRME'
        ).count(),
        'montant_total_collecte': Investissement.objects.filter(
            statut='CONFIRME'
        ).aggregate(total=Sum('montant'))['total'] or 0,
        'taux_reussite': round((projets_finances / max(total_projets, 1)) * 100, 1),
    }

    # Notifications récentes
    notifications = Notification.objects.all().order_by('-date_creation')[:5]

    # Investissements récents
    investissements_recents = Investissement.objects.filter(
        statut='CONFIRME'
    ).order_by('-date_investissement')[:4]

    # Éléments en attente
    utilisateurs_attente = Utilisateur.objects.filter(
        roles__statut='EN_ATTENTE_VALIDATION'
    ).distinct()[:5]

    projets_attente = Projet.objects.filter(
        statut='EN_ATTENTE_VALIDATION'
    ).order_by('-date_creation')[:5]

    documents_attente = Document.objects.filter(
        statut='EN_ATTENTE'
    ).order_by('-date_telechargement')[:5]

    return {
        'stats': stats,
        'notifications': notifications,
        'investissements_recents': investissements_recents,
        'utilisateurs_attente': utilisateurs_attente,
        'projets_attente': projets_attente,
        'documents_attente': documents_attente,
    }


def get_dashboard_promoteur_data(user):
    """
    Données pour le dashboard promoteur
    """
    # Projets du promoteur
    projets = user.projets.all()
    
    # Statistiques des projets
    stats_projets = {
        'total': projets.count(),
        'en_attente': projets.filter(statut='EN_ATTENTE_VALIDATION').count(),
        'valides': projets.filter(statut__in=['VALIDE', 'EN_COURS_FINANCEMENT']).count(),
        'finances': projets.filter(statut='FINANCE').count(),
        'en_realisation': projets.filter(statut='EN_REALISATION').count(),
        'termines': projets.filter(statut='TERMINE').count(),
    }
    
    # Montant total collecté
    montant_collecte = projets.aggregate(
        total=Sum('montant_collecte')
    )['total'] or 0
    
    # Nombre total d'investisseurs
    total_investisseurs = Investissement.objects.filter(
        projet__in=projets,
        statut='CONFIRME'
    ).values('investisseur').distinct().count()
    
    # Projets récents
    projets_recents = projets.order_by('-date_creation')[:5]
    
    # Investissements récents sur les projets du promoteur
    investissements_recents = Investissement.objects.filter(
        projet__in=projets,
        statut='CONFIRME'
    ).order_by('-date_investissement')[:10]
    
    return {
        'projets': projets,
        'stats_projets': stats_projets,
        'montant_collecte': montant_collecte,
        'total_investisseurs': total_investisseurs,
        'projets_recents': projets_recents,
        'investissements_recents': investissements_recents,
    }


def get_dashboard_investisseur_data(user):
    """
    Données pour le dashboard investisseur (pour référence)
    """
    # Investissements de l'utilisateur
    investissements = user.investissements.filter(statut='CONFIRME')
    
    # Statistiques des investissements
    stats_investissements = {
        'total': investissements.count(),
        'montant_total': investissements.aggregate(
            total=Sum('montant')
        )['total'] or 0,
    }
    
    # Projets dans lesquels l'utilisateur a investi
    projets_investis = Projet.objects.filter(
        investissements__investisseur=user,
        investissements__statut='CONFIRME'
    ).distinct()
    
    # Projets en cours vs terminés
    projets_en_cours = projets_investis.filter(
        statut__in=['EN_CAMPAGNE', 'EN_CONSTRUCTION']
    ).count()
    
    projets_termines = projets_investis.filter(
        statut__in=['FINANCE', 'TERMINE']
    ).count()
    
    # Investissements récents
    investissements_recents = investissements.order_by('-date_investissement')[:10]
    
    return {
        'stats_investissements': stats_investissements,
        'projets_investis': projets_investis,
        'projets_en_cours': projets_en_cours,
        'projets_termines': projets_termines,
        'investissements_recents': investissements_recents,
    }


def get_dashboard_attente_data(user):
    """
    Données pour le dashboard utilisateur en attente de validation
    """
    role_actif = user.get_role_actif()
    
    # Documents manquants
    from apps.documents.models import Document
    documents_utilisateur = Document.get_documents_utilisateur(user.id)
    
    # Types de documents requis selon le rôle
    if role_actif and role_actif.type == 'INVESTISSEUR':
        types_requis = ['JUSTIFICATIF_IDENTITE', 'JUSTIFICATIF_REVENU', 'JUSTIFICATIF_FONDS']
    elif role_actif and role_actif.type == 'PROMOTEUR':
        types_requis = ['JUSTIFICATIF_IDENTITE', 'JUSTIFICATIF_REVENU']
    else:
        types_requis = []
    
    documents_manquants = []
    for type_doc in types_requis:
        if not documents_utilisateur.filter(type=type_doc, statut='VALIDE').exists():
            documents_manquants.append(type_doc)
    
    # Projets à découvrir pendant l'attente
    projets_decouverte = Projet.objects.filter(
        statut__in=['VALIDE', 'EN_COURS_FINANCEMENT']
    ).order_by('-date_creation')[:6]
    
    return {
        'user': user,
        'documents_manquants': documents_manquants,
        'documents_utilisateur': documents_utilisateur,
        'projets_decouverte': projets_decouverte,
    }


def about(request):
    """
    Page À propos de la plateforme
    """
    return render(request, 'core/about.html')


def contact(request):
    """
    Page de contact
    """
    return render(request, 'core/contact.html')


def help_center(request):
    """
    Centre d'aide et FAQ
    """
    return render(request, 'core/help.html')