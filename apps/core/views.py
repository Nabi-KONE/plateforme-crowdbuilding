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
    Tableau de bord personnalisé selon le rôle de l'utilisateur
    """
    user = request.user
    role_actif = user.get_role_actif()
    
    context = {
        'user': user,
        'role_actif': role_actif,
    }
    
    if user.est_administrateur():
        # Dashboard administrateur
        context.update(get_dashboard_admin_data())
    elif user.est_promoteur():
        # Dashboard promoteur
        context.update(get_dashboard_promoteur_data(user))
    elif user.est_investisseur():
        # Dashboard investisseur
        context.update(get_dashboard_investisseur_data(user))
    else:
        # Dashboard utilisateur non validé
        context.update(get_dashboard_attente_data(user))
    
    return render(request, 'core/dashboard.html', context)


def get_dashboard_admin_data():
    """
    Données pour le dashboard administrateur
    """
    from django.db.models import Q
    
    # Statistiques générales
    stats = {
        'total_utilisateurs': Utilisateur.objects.count(),
        'utilisateurs_en_attente': Utilisateur.objects.filter(
            roles__statut='EN_ATTENTE_VALIDATION'
        ).distinct().count(),
        'total_projets': Projet.objects.count(),
        'projets_en_attente': Projet.objects.filter(
            statut='EN_ATTENTE_VALIDATION'
        ).count(),
        'total_investissements': Investissement.objects.filter(
            statut='CONFIRME'
        ).count(),
        'montant_total_collecte': Investissement.objects.filter(
            statut='CONFIRME'
        ).aggregate(total=Sum('montant'))['total'] or 0,
    }
    
    # Éléments en attente de validation
    utilisateurs_attente = Utilisateur.objects.filter(
        roles__statut='EN_ATTENTE_VALIDATION'
    ).distinct()[:10]
    
    projets_attente = Projet.objects.filter(
        statut='EN_ATTENTE_VALIDATION'
    ).order_by('-date_creation')[:10]
    
    # Documents en attente
    from apps.documents.models import Document
    documents_attente = Document.objects.filter(
        statut='EN_ATTENTE'
    ).order_by('-date_telechargement')[:10]
    
    return {
        'stats': stats,
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
    Données pour le dashboard investisseur
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
    
    # Rendement attendu total
    rendement_attendu = 0
    for investissement in investissements:
        rendement_attendu += investissement.calculer_rendement()
    
    # Investissements récents
    investissements_recents = investissements.order_by('-date_investissement')[:10]
    
    # Projets recommandés (autres projets valides)
    projets_recommandes = Projet.objects.filter(
        statut__in=['VALIDE', 'EN_COURS_FINANCEMENT']
    ).exclude(
        investissements__investisseur=user
    ).order_by('-date_creation')[:6]
    
    return {
        'investissements': investissements,
        'stats_investissements': stats_investissements,
        'projets_investis': projets_investis,
        'rendement_attendu': rendement_attendu,
        'investissements_recents': investissements_recents,
        'projets_recommandes': projets_recommandes,
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
    
    return {
        'documents_manquants': documents_manquants,
        'documents_utilisateur': documents_utilisateur,
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
