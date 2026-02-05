from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum, Max
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import TruncMonth
from collections import defaultdict


# Import des modèles
from apps.accounts.models import Utilisateur, Role, TypeRole, StatutRole
from apps.accounts.views import calculer_statistiques_utilisateurs
from apps.projects.models import Projet, CompteRendu, StatutProjet
from apps.investments.models import Investissement, StatutInvestissement, StatutTransaction, Transaction, TypeTransaction
from apps.documents.models import Document
from apps.notifications.models import Notification, TypeNotification
from django.db.models import Avg  # Pour les moyennes

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.db import transaction




def logout_view(request):
    logout(request)
    return redirect('accounts:login')  # page de login


from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test

# Vérifie que l'utilisateur est admin ou superuser
def is_admin(user):
    return user.is_superuser or user.is_staff

@login_required
@user_passes_test(is_admin)
def profile_view(request):
    """
    Affiche le profil de l'administrateur connecté
    """
    return render(request, 'admin/profile.html', {'user': request.user})



# =============================================================================
# GESTION DES UTILISATEURS (ADMIN)
# =============================================================================

@login_required
def admin_gestion_utilisateurs(request):
    """
    Vue principale pour la gestion des utilisateurs
    """
    if not request.user.est_administrateur():
        messages.error(request, 'Accès réservé aux administrateurs.')
        return redirect('core:dashboard')
    
    utilisateurs = Utilisateur.objects.prefetch_related('roles').all().order_by('-date_inscription')
    
    # Filtres
    search_query = request.GET.get('search', '')
    statut_filter = request.GET.get('statut', '')
    role_filter = request.GET.get('role', '')
    
    if search_query:
        utilisateurs = utilisateurs.filter(
            Q(nom__icontains=search_query) |
            Q(prenom__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(telephone__icontains=search_query)
        )
    
    if statut_filter:
        utilisateurs = utilisateurs.filter(roles__statut=statut_filter)
    
    if role_filter:
        utilisateurs = utilisateurs.filter(roles__type=role_filter)
    
    stats = calculer_statistiques_utilisateurs()
    
    # Stats projets pour sidebar
    stats_projets = {
        'projets_en_attente': Projet.objects.filter(statut='EN_ATTENTE_VALIDATION').count(),
    }
    
    context = {
        'utilisateurs': utilisateurs,
        'stats': stats,
        'stats_projets': stats_projets,
        'search_query': search_query,
        'statut_filter': statut_filter,
        'role_filter': role_filter,
        'count_resultats': utilisateurs.count(),
        'TypeRole': TypeRole,
        'StatutRole': StatutRole,
    }
    
    return render(request, 'admin/admin_users.html', context)

@login_required
@require_http_methods(["POST"])
def valider_utilisateur_ajax(request, user_id):
    """
    Valider un utilisateur via AJAX
    """
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès non autorisé.'
        }, status=403)
    
    try:
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        role_actif = utilisateur.get_role_actif()
        
        # Vérifier si tous les documents sont validés
        documents_utilisateur = Document.get_documents_utilisateur(utilisateur.id)
        documents_en_attente = documents_utilisateur.filter(statut='EN_ATTENTE')
        
        if documents_en_attente.exists():
            return JsonResponse({
                'success': False,
                'message': f'Impossible de valider le compte. {documents_en_attente.count()} document(s) en attente de validation.'
            })
        
        if role_actif and hasattr(role_actif, 'valider'):
            role_actif.valider(request.user)
            
            # Notification
            Notification.objects.create(
                utilisateur=utilisateur,
                titre="Compte validé ! 🎉",
                contenu=f"Félicitations {utilisateur.prenom} ! Votre compte a été validé. Vous pouvez maintenant accéder à toutes les fonctionnalités de la plateforme.",
                type='VALIDATION_COMPTE'
            )
            
            # Recalculer les stats
            stats = calculer_statistiques_utilisateurs()
            
            return JsonResponse({
                'success': True,
                'message': f'Le compte de {utilisateur.prenom} {utilisateur.nom} a été validé avec succès.',
                'stats': stats
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Aucun rôle en attente trouvé pour cet utilisateur.'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la validation: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def refuser_utilisateur_ajax(request, user_id):
    """
    Refuser un utilisateur via AJAX
    """
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès non autorisé.'
        }, status=403)
    
    try:
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        motif = request.POST.get('motif', 'Documents non conformes')
        
        role_actif = utilisateur.get_role_actif()
        
        if role_actif and hasattr(role_actif, 'refuser'):
            role_actif.refuser(request.user, motif)
            
            # Notification
            Notification.objects.create(
                utilisateur=utilisateur,
                titre="Compte refusé ❌",
                contenu=f"Votre compte a été refusé. Motif : {motif}",
                type='VALIDATION_COMPTE'
            )
            
            # Recalculer les stats
            stats = calculer_statistiques_utilisateurs()
            
            return JsonResponse({
                'success': True,
                'message': f'Le compte de {utilisateur.prenom} {utilisateur.nom} a été refusé.',
                'stats': stats
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Aucun rôle en attente trouvé pour cet utilisateur.'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du refus: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def suspendre_utilisateur_ajax(request, user_id):
    """
    Suspendre un utilisateur via AJAX
    """
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès non autorisé.'
        }, status=403)
    
    try:
        utilisateur = get_object_or_404(Utilisateur, id=user_id)
        motif = request.POST.get('motif', 'Suspension administrative')
        
        role_actif = utilisateur.get_role_actif()
        
        if role_actif and hasattr(role_actif, 'suspendre'):
            role_actif.suspendre(request.user, motif)
            
            # Notification
            Notification.objects.create(
                utilisateur=utilisateur,
                titre="Compte suspendu ⚠️",
                contenu=f"Votre compte a été suspendu. Motif : {motif}",
                type='SUSPENSION_COMPTE'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Le compte de {utilisateur.prenom} {utilisateur.nom} a été suspendu.'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Aucun rôle valide trouvé pour cet utilisateur.'
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la suspension: {str(e)}'
        }, status=500)

@login_required
def voir_details_utilisateur(request, user_id):
    """
    Voir les détails complets d'un utilisateur
    """
    if not request.user.est_administrateur():
        messages.error(request, 'Accès non autorisé.')
        return redirect('admin_perso:gestion_utilisateurs')
    
    utilisateur = get_object_or_404(Utilisateur, id=user_id)
    roles = utilisateur.roles.all().order_by('-date_creation')
    
    # Documents
    documents = Document.get_documents_utilisateur(utilisateur.id)

    # URL de retour
    next_url = request.GET.get('next', '')
    referer = request.META.get('HTTP_REFERER', '')
    
    if next_url:
        return_url = next_url
    elif referer and '/projects/' in referer:
        return_url = referer
    else:
        return_url = reverse('admin_perso:gestion_utilisateurs')
    
    # Statistiques selon le rôle
    stats_projets = {}
    stats_investissements = {}
    
    role_actif = utilisateur.get_role_actif()
    if role_actif and hasattr(role_actif, 'type'):
        if role_actif.type == TypeRole.PROMOTEUR:
            projets_utilisateur = utilisateur.projets.all()
            montant_leve = projets_utilisateur.aggregate(
                total=Sum('montant_collecte')
            )['total'] or 0
            
            stats_projets = {
                'total': projets_utilisateur.count(),
                'montant_leve': montant_leve,
                'taux_reussite': 75,
            }
                
        elif role_actif.type == TypeRole.INVESTISSEUR:
            investissements_utilisateur = utilisateur.investissements.filter(statut='CONFIRME')
            montant_total = investissements_utilisateur.aggregate(
                total=Sum('montant')
            )['total'] or 0
            
            stats_investissements = {
                'total': investissements_utilisateur.count(),
                'montant_total': montant_total,
                'projets_investis': investissements_utilisateur.values('projet').distinct().count(),
            }
    
    # Historique
    historique = []
    
    historique.append({
        'titre': 'Inscription sur la plateforme',
        'description': f'Création du compte {role_actif.get_type_display() if role_actif else "Utilisateur"}',
        'date': utilisateur.date_inscription
    })
    
    if utilisateur.last_login:
        historique.append({
            'titre': 'Dernière connexion',
            'description': 'Connexion à la plateforme',
            'date': utilisateur.last_login
        })
    
    for role in roles:
        historique.append({
            'titre': f'Rôle {role.get_type_display()} {role.get_statut_display().lower()}',
            'description': f'Statut du rôle défini à {role.get_statut_display()}',
            'date': role.date_creation
        })
    
    notifications_importantes = Notification.objects.filter(
        utilisateur=utilisateur,
        action_requise=True  
    ).order_by('-date_creation')[:5]
    
    for notif in notifications_importantes:
        historique.append({
            'titre': notif.titre,
            'description': notif.contenu,
            'date': notif.date_creation
        })
    
    historique.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'utilisateur': utilisateur,
        'roles': roles,
        'documents': documents,
        'stats_projets': stats_projets,
        'stats_investissements': stats_investissements,
        'historique': historique[:10],
        'return_url': return_url,  
    }
    
    return render(request, 'admin/admin_user_details.html', context)

# =============================================================================
# GESTION DES PROJETS (ADMIN)
# =============================================================================

@login_required
def admin_gestion_projets(request):
    """
    Vue principale pour la gestion des projets par l'admin
    """
    if not request.user.est_administrateur():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('core:dashboard')
    
    projets = Projet.objects.select_related('promoteur').prefetch_related('images').all().order_by('-date_creation')
    
    search_query = request.GET.get('search', '')
    statut_filter = request.GET.get('statut', '')
    categorie_filter = request.GET.get('categorie', '')
    
    if search_query:
        projets = projets.filter(
            Q(titre__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(promoteur__nom__icontains=search_query) |
            Q(promoteur__prenom__icontains=search_query) |
            Q(reference__icontains=search_query)
        )
    
    if statut_filter:
        projets = projets.filter(statut=statut_filter)
    
    if categorie_filter:
        projets = projets.filter(categorie=categorie_filter)
    
    stats = {
        'total': Projet.objects.count(),
        'en_attente': Projet.objects.filter(statut='EN_ATTENTE_VALIDATION').count(),
        'en_campagne': Projet.objects.filter(statut='EN_CAMPAGNE').count(),
        'finances': Projet.objects.filter(statut='FINANCE').count(),
        'refuses': Projet.objects.filter(statut='REFUSE').count(),
    }
    
    context = {
        'projets': projets,
        'stats': stats,
        'search_query': search_query,
        'statut_filter': statut_filter,
        'categorie_filter': categorie_filter,
    }
    
    return render(request, 'admin/projets/liste.html', context)  

@login_required
@require_http_methods(["POST"])
def valider_projet_ajax(request, project_id):
    """Valider un projet via AJAX"""
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)
    
    try:
        projet = get_object_or_404(Projet, id=project_id)
        
        # Valider le projet
        projet.valider(request.user)
        projet.lancer_campagne()
        
        # Notification pour le promoteur
        Notification.objects.create(
            utilisateur=projet.promoteur,
            titre="Projet validé",
            contenu=(
                f"Bonjour {projet.promoteur.prenom},\n\n"
                f"Votre projet « {projet.titre} » a été validé avec succès.\n"
                f"Il est maintenant visible sur la plateforme."
            ),
            type=TypeNotification.VALIDATION_PROJET,
            projet=projet
        )
 
        # Email de notification (optionnel)
        try:
            send_mail(
                subject=f"crowdBuilding - Votre projet '{projet.titre}' a été validé",
                message=f"""
                Bonjour {projet.promoteur.prenom},
                
                Félicitations ! Votre projet "{projet.titre}" a été validé par notre équipe.
                
                Votre projet est maintenant visible sur la plateforme et peut recevoir des investissements.
                
                Référence : {projet.reference}
                Montant cible : {projet.montant_total:,} FCFA
                
                Cordialement,
                L'équipe crowdBuilding
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[projet.promoteur.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi email: {e}")
        
        return JsonResponse({
            'success': True,
            'message': f'Le projet "{projet.titre}" a été validé avec succès.',
            'nouveau_statut': projet.get_statut_display(),
            'statut_color': projet.get_statut_color()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la validation: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def refuser_projet_ajax(request, project_id):
    """Refuser un projet via AJAX"""
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)
    
    try:
        projet = get_object_or_404(Projet, id=project_id)
        motif = request.POST.get('motif', 'Documents incomplets ou non conformes')
        
        if not motif:
            return JsonResponse({
                'success': False,
                'message': 'Veuillez fournir un motif de refus.'
            })
        
        # Refuser le projet
        projet.refuser(request.user, motif)
        
        # Notification pour le promoteur
        Notification.objects.create(
            utilisateur=projet.promoteur,
            titre="❌ Projet refusé",
            contenu=(
                f"Bonjour {projet.promoteur.prenom},\n\n"
                f"Votre projet « {projet.titre} » a été refusé.\n\n"
                f"Motif : {motif}"
            ),
            type=TypeNotification.VALIDATION_PROJET,
            projet=projet,
            action_requise=True
        )

        
        return JsonResponse({
            'success': True,
            'message': f'Le projet "{projet.titre}" a été refusé.',
            'nouveau_statut': projet.get_statut_display(),
            'statut_color': projet.get_statut_color()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du refus: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def demarrer_execution(request, project_id):
    """Démarrer l'exécution d'un projet"""
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)
    
    try:
        projet = get_object_or_404(Projet, id=project_id)
        
        if projet.statut != 'FINANCE':
            return JsonResponse({
                'success': False,
                'message': 'Le projet doit être entièrement financé pour démarrer l\'exécution.'
            })
        
        projet.statut = 'EN_COURS_EXECUTION'
        projet.date_debut_execution = timezone.now().date()
        projet.save()
        
        # Notification
        Notification.objects.create(
            utilisateur=projet.promoteur,
            titre="🚀 Début d'exécution",
            contenu=f"L'exécution de votre projet '{projet.titre}' a démarré !",
            type='DEBUT_EXECUTION'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'L\'exécution du projet "{projet.titre}" a démarré.',
            'nouveau_statut': projet.get_statut_display()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du démarrage: {str(e)}'
        }, status=500)

@login_required
@require_http_methods(["POST"])
def terminer_projet(request, project_id):
    """Marquer un projet comme terminé"""
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)
    
    try:
        projet = get_object_or_404(Projet, id=project_id)
        
        projet.statut = 'TERMINE'
        projet.save()
        
        # Notification
        Notification.objects.create(
            utilisateur=projet.promoteur,
            titre="🏁 Projet terminé",
            contenu=f"Félicitations ! Votre projet '{projet.titre}' est marqué comme terminé.",
            type='PROJET_TERMINE'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Le projet "{projet.titre}" a été marqué comme terminé.',
            'nouveau_statut': projet.get_statut_display()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=500)

# =============================================================================
# GESTION DES COMPTES RENDUS (ADMIN)
# =============================================================================

@login_required
def admin_liste_comptes_rendus(request):
    """
    Liste des comptes rendus pour l'administration - VERSION UNIQUE
    """
    if not request.user.est_administrateur():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('core:dashboard')
    
    # Filtres
    statut_filter = request.GET.get('statut', '')
    projet_filter = request.GET.get('projet', '')
    search_query = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Query de base
    comptes_rendus = CompteRendu.objects.select_related(
        'projet', 'projet__promoteur', 'etape', 'administrateur_validateur'
    ).prefetch_related('images').order_by('-date_creation')
    
    # Appliquer les filtres
    if statut_filter:
        comptes_rendus = comptes_rendus.filter(statut=statut_filter)
    
    if projet_filter:
        comptes_rendus = comptes_rendus.filter(projet_id=projet_filter)
    
    if search_query:
        comptes_rendus = comptes_rendus.filter(
            Q(titre__icontains=search_query) |
            Q(contenu__icontains=search_query) |
            Q(projet__titre__icontains=search_query) |
            Q(projet__promoteur__nom__icontains=search_query) |
            Q(projet__promoteur__prenom__icontains=search_query)
        )
    
    # Filtres de date
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            comptes_rendus = comptes_rendus.filter(date_creation__date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            comptes_rendus = comptes_rendus.filter(date_creation__date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Pagination
    paginator = Paginator(comptes_rendus, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total': CompteRendu.objects.count(),
        'en_attente': CompteRendu.objects.filter(statut='EN_ATTENTE_VALIDATION').count(),
        'valides': CompteRendu.objects.filter(statut='VALIDE').count(),
        'rejetes': CompteRendu.objects.filter(statut='REJETE').count(),
        'attente_recent': CompteRendu.objects.filter(
            statut='EN_ATTENTE_VALIDATION',
            date_creation__gte=timezone.now() - timedelta(days=3)
        ).count(),
    }
    
    # Projets pour le filtre
    projets_avec_cr = Projet.objects.filter(
        comptes_rendus__isnull=False
    ).distinct().order_by('titre')
    
    context = {
        'comptes_rendus': page_obj,
        'page_obj': page_obj,
        'stats': stats,
        'projets': projets_avec_cr,
        'statut_filter': statut_filter,
        'projet_filter': projet_filter,
        'search_query': search_query,
        'date_from': date_from,
        'date_to': date_to,
        'statuts_choices': CompteRendu.STATUT_CHOICES,
    }
    
    return render(request, 'admin/comptes_rendus/liste.html', context)

@login_required
def admin_detail_compte_rendu(request, cr_id):
    if not request.user.est_administrateur():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('core:dashboard')

    compte_rendu = get_object_or_404(
        CompteRendu.objects.select_related(
            'projet',
            'projet__promoteur',
            'etape',
            'administrateur_validateur'
        ).prefetch_related(
            'images',
            'projet__etapes'
        ),
        id=cr_id
    )

    images = compte_rendu.images.all().order_by('ordre')

    comptes_rendus_precedents = CompteRendu.objects.filter(
        projet=compte_rendu.projet,
        date_creation__lt=compte_rendu.date_creation,
        statut='VALIDE'
    ).order_by('-date_creation')[:5]

    # Avancement global
    etapes_terminees = 0
    total_etapes = 0
    avancement_global = 0

    if compte_rendu.projet.etapes.exists():
        etapes_terminees = compte_rendu.projet.etapes.filter(terminee=True).count()
        total_etapes = compte_rendu.projet.etapes.count()
        if total_etapes > 0:
            avancement_global = (etapes_terminees / total_etapes) * 100

    # Étape précédente
    etape_precedente = None
    if compte_rendu.etape:
        etape_precedente = compte_rendu.projet.etapes.filter(
            ordre__lt=compte_rendu.etape.ordre,
            terminee=True
        ).order_by('-ordre').first()

    # Temps de lecture
    temps_lecture = max(1, len(compte_rendu.contenu) // 200)

    total_comptes_rendus = compte_rendu.projet.comptes_rendus.count()
    comptes_rendus_valides = compte_rendu.projet.comptes_rendus.filter(statut='VALIDE').count()




    context = {
        'compte_rendu': compte_rendu,
        'images': images,
        'comptes_rendus_precedents': comptes_rendus_precedents,
        'etapes_terminees': etapes_terminees,
        'total_etapes': total_etapes,
        'avancement_global': avancement_global,
        'etape_precedente': etape_precedente,
        'temps_lecture': temps_lecture,
        'peut_valider': compte_rendu.statut == 'EN_ATTENTE_VALIDATION',
        'peut_rejeter': compte_rendu.statut == 'EN_ATTENTE_VALIDATION',
        'peut_demander_modification': compte_rendu.statut == 'EN_ATTENTE_VALIDATION',
        'total_comptes_rendus': total_comptes_rendus,
        'comptes_rendus_valides': comptes_rendus_valides,
        'temps_lecture': temps_lecture,


    }

    return render(request, 'admin/comptes_rendus/detail.html', context)



@login_required
@user_passes_test(is_admin)
@transaction.atomic
def admin_valider_compte_rendu(request, cr_id):

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

    compte_rendu = get_object_or_404(
        CompteRendu.objects.select_for_update(),
        id=cr_id
    )

    # 🔒 Vérification de l’état
    if compte_rendu.statut != 'EN_ATTENTE_VALIDATION':
        return JsonResponse({
            'success': False,
            'message': "Ce compte rendu ne peut plus être validé."
        }, status=400)

    compte_rendu.statut = 'VALIDE'
    compte_rendu.administrateur_validateur = request.user
    compte_rendu.date_validation = timezone.now()
    compte_rendu.date_publication = timezone.now()
    compte_rendu.motif_rejet = ''

    compte_rendu.save(update_fields=[
        'statut',
        'administrateur_validateur',
        'date_validation',
        'date_publication',
        'motif_rejet'
    ])

    return JsonResponse({
        'success': True,
        'message': 'Compte rendu validé avec succès.',
        'redirect_url': '/admin/comptes-rendus/'
    })


@login_required
def admin_rejeter_compte_rendu(request, cr_id):
    """
    Vue pour permettre à l'admin de rejeter un compte rendu.
    Attend un POST avec le champ 'motif'.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'}, status=405)

    compte_rendu = get_object_or_404(CompteRendu, id=cr_id)

    # Vérifier que le compte rendu est en attente
    if compte_rendu.statut != 'EN_ATTENTE_VALIDATION':
        return JsonResponse({
            'success': False,
            'message': "Ce compte rendu ne peut pas être rejeté car il n'est pas en attente de validation."
        })

    # Récupération du motif depuis le JSON
    import json
    try:
        data = json.loads(request.body)
        motif = data.get('motif', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Données invalides.'}, status=400)

    # Vérifications
    if not motif or len(motif) < 10:
        return JsonResponse({
            'success': False,
            'message': 'Le motif doit contenir au moins 10 caractères.'
        })

    # Mise à jour du compte rendu
    compte_rendu.statut = 'REJETE'
    compte_rendu.administrateur_validateur = request.user
    compte_rendu.date_validation = timezone.now()
    compte_rendu.motif_rejet = motif  # ⬅️ mettre le motif fourni
    compte_rendu.save(update_fields=[
        'statut',
        'administrateur_validateur',
        'date_validation',
        'motif_rejet'
    ])

    return JsonResponse({
        'success': True,
        'message': 'Le compte rendu a été rejeté avec succès.',
        'redirect_url': '/admin-perso/comptes-rendus/'  # ou redirection vers la liste
    })


@login_required
def admin_comptes_rendus_projet(request, project_id):
    """Liste des comptes rendus d'un projet spécifique (admin)"""
    if not request.user.est_administrateur():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('core:dashboard')
    
    projet = get_object_or_404(Projet, id=project_id)
    comptes_rendus = CompteRendu.objects.filter(
        projet=projet
    ).select_related('etape', 'administrateur_validateur').order_by('-date_creation')
    
    # Statistiques du projet
    stats_projet = {
        'total_cr': comptes_rendus.count(),
        'valides': comptes_rendus.filter(statut='VALIDE').count(),
        'en_attente': comptes_rendus.filter(statut='EN_ATTENTE_VALIDATION').count(),
        'rejetes': comptes_rendus.filter(statut='REJETE').count(),
    }
    
    context = {
        'projet': projet,
        'comptes_rendus': comptes_rendus,
        'stats_projet': stats_projet,
    }
    
    return render(request, 'admin/comptes_rendus/projet.html', context)

# =============================================================================
# GESTION DES INVESTISSEMENTS (ADMIN)
# =============================================================================

@staff_member_required
def admin_gestion_investissements(request):
    """
    Vue pour la gestion des investissements côté administrateur
    """
    try:
        # Filtres
        status_filter = request.GET.get('status', '')
        project_filter = request.GET.get('projet', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        search_query = request.GET.get('search', '')
        
        # Construction de la requête
        queryset = Investissement.objects.select_related(
            'investisseur', 'projet'
        ).order_by('-date_investissement')
        
        if status_filter in dict(StatutInvestissement.choices):
            queryset = queryset.filter(statut=status_filter)

        if project_filter:
            queryset = queryset.filter(projet_id=project_filter)
        
        if date_from:
            queryset = queryset.filter(date_investissement__date__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(date_investissement__date__lte=date_to)
        
        if search_query:
            queryset = queryset.filter(
                Q(investisseur__nom_complet__icontains=search_query) |
                Q(projet__titre__icontains=search_query) |
                Q(reference__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(queryset, 20)
        page = request.GET.get('page', 1)
        
        try:
            investissements = paginator.page(page)
        except PageNotAnInteger:
            investissements = paginator.page(1)
        except EmptyPage:
            investissements = paginator.page(paginator.num_pages)
        
        # Statistiques
        stats_filtered = queryset.aggregate(
            total_sum=Sum('montant'),
            total_count=Count('id'),

            pending_payment_count=Count(
                'id',
                filter=Q(statut=StatutInvestissement.EN_ATTENTE_PAIEMENT)
            ),

            payment_received_count=Count(
                'id',
                filter=Q(statut=StatutInvestissement.PAIEMENT_RECU)
            ),

            confirmed_count=Count(
                'id',
                filter=Q(statut=StatutInvestissement.CONFIRME)
            ),

            refunded_count=Count(
                'id',
                filter=Q(statut=StatutInvestissement.REMBOURSE)
            ),

            rejected_count=Count(
                'id',
                filter=Q(statut=StatutInvestissement.REJETE)
            ),

            max_amount=Max('montant')
        )

        
        stats_global = Investissement.objects.aggregate(
            total_sum_global=Sum('montant'),
            total_count_global=Count('id')
        )
        
        total_investissements = stats_filtered['total_sum'] or Decimal('0')
        total_count = stats_filtered['total_count'] or 0
        investissements_en_attente_paiement = (
            stats_filtered['pending_payment_count'] or 0
        )

        investissements_payes = (
            stats_filtered['payment_received_count'] or 0
        )

        
        # Statistiques du mois
        maintenant = timezone.now()
        mois_debut = timezone.datetime(maintenant.year, maintenant.month, 1)
        mois_fin = mois_debut + timezone.timedelta(days=32)
        mois_fin = mois_fin.replace(day=1) - timezone.timedelta(days=1)
        
        investissements_mois = Investissement.objects.filter(
            date_investissement__date__gte=mois_debut.date(),
            date_investissement__date__lte=mois_fin.date(),
            statut__in=[
                StatutInvestissement.PAIEMENT_RECU,
                StatutInvestissement.CONFIRME
            ]
        ).aggregate(
            mois_sum=Sum('montant')
        )['mois_sum'] or Decimal('0')

        
        # Moyennes
        moyenne_investissement = (total_investissements / total_count) if total_count > 0 else Decimal('0')
        
        # Autres stats
        total_projets = Projet.objects.filter(
            investissements__in=queryset
        ).distinct().count() if queryset.exists() else 0
        
        investisseurs_actifs = Utilisateur.objects.filter(
            investissements__in=queryset
        ).distinct().count() if queryset.exists() else 0
        
        taux_completion = round(
            (stats_filtered['confirmed_count'] / total_count * 100) if total_count > 0 else 0, 
            1
        )
        
        top_projets = Projet.objects.filter(
            investissements__in=queryset
        ).annotate(
            total_investi=Sum('investissements__montant'),
            investisseur_count=Count('investissements__investisseur', distinct=True)
        ).filter(
            total_investi__isnull=False
        ).order_by('-total_investi')[:5]
        
        investissement_max = stats_filtered['max_amount'] or Decimal('0')
        
        # =============================
        # 📊 DONNÉES GRAPHE RÉELLES
        # =============================

        # On ne prend QUE les investissements confirmés
        invest_qs = Investissement.objects.filter(
            statut=StatutInvestissement.CONFIRME
        )

        # Remboursements réels
        refund_qs = Transaction.objects.filter(
            type=TypeTransaction.REMBOURSEMENT,
            statut=StatutTransaction.VALIDEE
        )

        # Filtre par projet si sélectionné
        if project_filter:
            invest_qs = invest_qs.filter(projet_id=project_filter)
            refund_qs = refund_qs.filter(investissement__projet_id=project_filter)

        # Agrégation mensuelle
        invest_data = (
            invest_qs
            .annotate(mois=TruncMonth('date_investissement'))
            .values('mois')
            .annotate(total=Sum('montant'))
            .order_by('mois')
        )

        refund_data = (
            refund_qs
            .annotate(mois=TruncMonth('date_transaction'))
            .values('mois')
            .annotate(total=Sum('montant'))
            .order_by('mois')
        )

        # Fusion mois
        monthly = defaultdict(lambda: {'invest': 0, 'refund': 0})

        for row in invest_data:
            key = row['mois'].strftime('%b %Y')
            monthly[key]['invest'] = float(row['total'])

        for row in refund_data:
            key = row['mois'].strftime('%b %Y')
            monthly[key]['refund'] = float(row['total'])

        chart_labels = list(monthly.keys())
        chart_invest = [monthly[m]['invest'] for m in chart_labels]
        chart_refund = [monthly[m]['refund'] for m in chart_labels]

        
        # Projets pour filtre
        projets = Projet.objects.filter(
            Q(statut='EN_CAMPAGNE') | Q(statut='FINANCE')
        ).order_by('-date_creation')
        
        # Évolution
        mois_precedent_debut = (mois_debut - timezone.timedelta(days=32)).replace(day=1)
        mois_precedent_fin = mois_debut - timezone.timedelta(days=1)
        
        investissements_mois_precedent = Investissement.objects.filter(
            date_investissement__date__gte=mois_precedent_debut.date(),
            date_investissement__date__lte=mois_precedent_fin.date(),
            statut__in=[
                StatutInvestissement.PAIEMENT_RECU,
                StatutInvestissement.CONFIRME
            ]
        ).aggregate(
            total=Sum('montant')
        )['total'] or Decimal('0')

        
        evolution_mois = 0
        if investissements_mois_precedent > 0:
            evolution_mois = ((investissements_mois - investissements_mois_precedent) / investissements_mois_precedent * 100)
        
        context = {
            'investissements': investissements,
            'projets': projets,
            'total_investissements': total_investissements,
            'investissements_mois': investissements_mois,
            'investissements_en_attente_paiement': investissements_en_attente_paiement,
            'investissements_payes': investissements_payes,
            'moyenne_investissement': moyenne_investissement,
            'total_projets': total_projets,
            'investisseurs_actifs': investisseurs_actifs,
            'taux_completion': taux_completion,
            'top_projets': top_projets,
            'investissement_max': investissement_max,
            'chart_labels': chart_labels,
            'chart_invest': chart_invest,
            'chart_refund': chart_refund,
            'evolution_mois': round(evolution_mois, 1),
            'current_status': status_filter,
            'current_project': project_filter,
            'current_date_from': date_from,
            'current_date_to': date_to,
            'current_search': search_query,
            'total_count': total_count,
            'confirmed_count': stats_filtered['confirmed_count'] or 0,
            'attente_paiement_count': stats_filtered['attente_paiement_count'] or 0,
            'paiement_recu_count': stats_filtered['paiement_recu_count'] or 0,
            'confirmed_count': stats_filtered['confirmed_count'] or 0,
            'refunded_count': stats_filtered['refunded_count'] or 0,
            'rejected_count': stats_filtered['rejected_count'] or 0,
            'total_investissements_global': stats_global['total_sum_global'] or Decimal('0'),
            'total_count_global': stats_global['total_count_global'] or 0,
        }
        
        return render(request, 'admin/admin_gestion_investissements.html', context)
        
    except Exception as e:
        print(f"Erreur dans admin_gestion_investissements: {e}")
        
        context = {
            'investissements': [],
            'projets': Projet.objects.all(),
            'total_investissements': Decimal('0'),
            'investissements_mois': Decimal('0'),
            'investissements_en_attente': 0,
            'moyenne_investissement': Decimal('0'),
            'total_projets': 0,
            'investisseurs_actifs': 0,
            'taux_completion': 0,
            'top_projets': [],
            'investissement_max': Decimal('0'),
            'mois_liste': [],
            'montants_mois': [],
            'evolution_mois': 0,
            'error': str(e),
        }
        
        return render(request, 'admin/admin_gestion_investissements.html', context)

@staff_member_required
@require_http_methods(["POST"])
def valider_investissement(request, investment_id):
    """
    Valider un investissement (admin)
    """
    try:
        investissement = get_object_or_404(Investissement, id=investment_id)
        
        if investissement.statut != StatutInvestissement.PAIEMENT_RECU.value:
            return JsonResponse({
                'success': False,
                'message': "Le paiement doit être reçu avant validation."
            })

        # Valider l'investissement
        investissement.confirmer_par_admin()
        
        # Notification à l'investisseur
        Notification.objects.create(
            utilisateur=investissement.investisseur,
            titre="✅ Investissement confirmé !",
            contenu=f"Votre investissement {investissement.reference} de {investissement.montant:,.0f} FCFA dans le projet '{investissement.projet.titre}' a été confirmé.",
            type='INVESTISSEMENT_CONFIRME'
        )
        
        # Notification au promoteur
        Notification.objects.create(
            utilisateur=investissement.projet.promoteur,
            titre="🎉 Investissement confirmé !",
            contenu=f"L'investissement {investissement.reference} de {investissement.montant:,.0f} FCFA dans votre projet '{investissement.projet.titre}' a été confirmé.",
            type='INVESTISSEMENT_RECU'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Investissement {investissement.reference} confirmé avec succès.',
            'new_status': investissement.get_statut_display(),
            'investment_id': investissement.id,
            'reference': investissement.reference
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': "Une erreur interne est survenue lors de la validation."
        }, status=500)


@staff_member_required
@require_http_methods(["POST"])
def rejeter_investissement(request, investment_id):

    investissement = get_object_or_404(Investissement, id=investment_id)
    raison = request.POST.get('raison', 'Raison non spécifiée')

    try:
        investissement.rejeter_avec_remboursement(raison)

        Notification.objects.create(
            utilisateur=investissement.investisseur,
            titre="❌ Investissement rejeté",
            contenu=f"Votre investissement {investissement.reference} a été rejeté. {raison}",
            type="INVESTISSEMENT_REJETE"
        )

        return JsonResponse({
            'success': True,
            'message': "Investissement rejeté avec succès."
        })

    except ValueError as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


# =============================================================================
# GESTION DES DOCUMENTS (ADMIN)
# =============================================================================

@staff_member_required
def validate_documents_list(request):
    """
    Vue pour lister tous les documents en attente de validation
    """
    documents_en_attente = Document.get_documents_en_attente()
    
    documents_data = []
    for document in documents_en_attente:
        proprietaire = document.get_proprietaire()
        documents_data.append({
            'document': document,
            'proprietaire': proprietaire,
            'utilisateur_info': f"{proprietaire.get_full_name() or proprietaire.email} ({proprietaire.get_role_actif_display()})" if proprietaire else "Utilisateur inconnu"
        })
    
    context = {
        'documents_data': documents_data,
    }
    
    return render(request, 'admin/validation_documents.html', context) 

@staff_member_required
def validate_document_action(request, document_id):
    """
    Vue pour valider ou refuser un document (action AJAX)
    """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        document = get_object_or_404(Document, id=document_id)
        action = request.POST.get('action')
        motif = request.POST.get('motif', '')
        
        try:
            if action == 'valider':
                document.valider(request.user)
                return JsonResponse({
                    'success': True,
                    'message': f'Document "{document.nom}" validé avec succès!'
                })
            elif action == 'refuser':
                if not motif:
                    return JsonResponse({
                        'success': False,
                        'message': 'Veuillez fournir un motif de refus.'
                    })
                document.refuser(request.user, motif)
                return JsonResponse({
                    'success': True,
                    'message': f'Document "{document.nom}" refusé avec succès!'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Action non reconnue.'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Requête invalide.'
    })


# =============================================================================
# DASHBOARD ADMIN PRINCIPAL
# =============================================================================

@login_required
def admin_dashboard(request):
    """
    Dashboard spécifique pour admin
    """
    if not request.user.est_administrateur():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('core:dashboard')

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

    context = {
        'stats': stats,
        'notifications': notifications,
        'investissements_recents': investissements_recents,
        'utilisateurs_attente': utilisateurs_attente,
        'projets_attente': projets_attente,
        'documents_attente': documents_attente,
    }
    
    return render(request, 'admin/dashboard.html', context) 

# =============================================================================
# VALIDATION PROJET (FORMULAIRE COMPLET)
# =============================================================================

@login_required
def validate_project_admin(request, project_id):
    """
    Validation d'un projet par l'administrateur (formulaire complet)
    """
    if not request.user.est_administrateur():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('core:dashboard')
    
    projet = get_object_or_404(Projet, id=project_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        motif = request.POST.get('motif', '')
        
        if action == 'valider':
            projet.valider(request.user)
            projet.lancer_campagne()
            
            # Créer des notifications
            Notification.objects.create(
                utilisateur=projet.promoteur,
                titre="🎉 Projet validé !",
                contenu=f"Félicitations ! Votre projet '{projet.titre}' a été validé et la campagne est lancée !",
                type='VALIDATION_PROJET',
                important=True
            )
            
            messages.success(request, f'Le projet "{projet.titre}" a été validé et la campagne est lancée !')
            
        elif action == 'completer':
            if not motif:
                motif = "Merci de préciser au moins les grandes étapes avant validation."
            
            projet.statut = StatutProjet.A_COMPLETER
            projet.motif_refus = motif
            projet.save()
            
            Notification.objects.create(
                utilisateur=projet.promoteur,
                titre="📝 Projet à compléter",
                contenu=f"Votre projet '{projet.titre}' nécessite des compléments. Motif : {motif}",
                type='PROJET_A_COMPLETER',
                important=True
            )
            
            messages.success(request, f'Le projet "{projet.titre}" a été renvoyé pour complément.')
            
        elif action == 'refuser':
            if not motif:
                messages.error(request, "Veuillez fournir un motif de refus.")
            else:
                projet.refuser(request.user, motif)
                
                Notification.objects.create(
                    utilisateur=projet.promoteur,
                    titre="❌ Projet refusé",
                    contenu=f"Votre projet '{projet.titre}' a été refusé. Motif : {motif}",
                    type='REFUS_PROJET',
                    important=True
                )
                
                messages.success(request, f'Le projet "{projet.titre}" a été refusé.')
        
        return render(request, 'admin/projets/validate_admin.html', context) 
    
    context = {
        'projet': projet,
    }
    
    return render(request, 'admin/projets/validate_admin.html', context)

# =============================================================================
# PUBLICATION PROJET
# =============================================================================

@login_required
@require_http_methods(["POST"])
def partager_projet(request, project_id):
    """
    Publier un projet sur le site public
    """
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)
    
    try:
        projet = get_object_or_404(Projet, id=project_id)
        
        # Vérifier que le projet est validé
        if projet.statut != StatutProjet.VALIDE:
            return JsonResponse({
                'success': False,
                'message': 'Le projet doit être validé avant d\'être publié.'
            })
        
        # Lancer la campagne (rendre le projet public)
        projet.lancer_campagne()
        
        # Notification pour le promoteur
        Notification.objects.create(
            utilisateur=projet.promoteur,
            titre="🎉 Projet publié !",
            contenu=f"Félicitations ! Votre projet '{projet.titre}' a été publié sur la plateforme et est maintenant visible par les investisseurs.",
            type='PUBLICATION_PROJET'
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Le projet "{projet.titre}" a été publié avec succès et est maintenant visible sur le site.',
            'nouveau_statut': projet.get_statut_display(),
            'statut_color': projet.get_statut_color()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la publication: {str(e)}'
        })

# =============================================================================
# SUSPENSION PROJET
# =============================================================================

@login_required
@require_http_methods(["POST"])
def suspendre_projet(request, project_id):

    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)

    try:
        projet = get_object_or_404(Projet, id=project_id)
        motif = request.POST.get('motif', 'Suspension administrative')

        # 🔴 SUSPENSION
        if projet.statut != StatutProjet.SUSPENDU:
            projet.statut_precedent = projet.statut
            projet.statut = StatutProjet.SUSPENDU
            projet.motif_suspension = motif
            projet.save()

            Notification.objects.create(
                utilisateur=projet.promoteur,
                titre="⏸️ Projet suspendu",
                contenu=f"Votre projet « {projet.titre} » a été suspendu.\nMotif : {motif}",
                type=TypeNotification.SUSPENSION_PROJET,
                projet=projet,
                action_requise=True
            )

            return JsonResponse({
                'success': True,
                'message': f'Projet "{projet.titre}" suspendu.',
                'nouveau_statut': projet.get_statut_display(),
                'statut_color': 'danger'
            })

        # ▶️ RÉACTIVATION
        projet.statut = projet.statut_precedent or StatutProjet.EN_CAMPAGNE
        projet.statut_precedent = None
        projet.motif_suspension = ''
        projet.save()

        Notification.objects.create(
            utilisateur=projet.promoteur,
            titre="▶️ Projet réactivé",
            contenu=f"Votre projet « {projet.titre} » a été réactivé.",
            type=TypeNotification.REACTIVATION_PROJET,
            projet=projet
        )

        return JsonResponse({
            'success': True,
            'message': f'Projet "{projet.titre}" réactivé.',
            'nouveau_statut': projet.get_statut_display(),
            'statut_color': projet.get_statut_color()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur serveur : {str(e)}'
        }, status=500)


# =============================================================================
# VALIDATION DOCUMENT AJAX
# =============================================================================

@login_required
@require_http_methods(["POST"])
def valider_document_ajax(request, document_id):
    """Valider un document via AJAX"""
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)
    
    try:
        document = get_object_or_404(Document, id=document_id)
        
        # Utiliser la méthode existante du modèle Document
        document.valider(request.user)
        
        # Récupérer le propriétaire pour la notification
        proprietaire = document.get_proprietaire()
        
        # Notification au propriétaire
        if proprietaire:
            if hasattr(proprietaire, 'email'):  # C'est un utilisateur
                Notification.objects.create(
                    utilisateur=proprietaire,
                    titre="✅ Document validé",
                    contenu=f"Votre document '{document.nom}' a été validé.",
                    type='VALIDATION_DOCUMENT'
                )
            elif hasattr(proprietaire, 'promoteur'):  # C'est un projet
                Notification.objects.create(
                    utilisateur=proprietaire.promoteur,
                    titre="✅ Document validé",
                    contenu=f"Votre document '{document.nom}' pour le projet '{proprietaire.titre}' a été validé.",
                    type='VALIDATION_DOCUMENT'
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Le document "{document.nom}" a été validé.',
            'document_id': document.id,
            'nouveau_statut': document.get_statut_display()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la validation: {str(e)}'
        }, status=500)

# =============================================================================
# REFUS DOCUMENT AJAX
# =============================================================================

@login_required
@require_http_methods(["POST"])
def refuser_document_ajax(request, document_id):
    """Refuser un document via AJAX"""
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)
    
    try:
        document = get_object_or_404(Document, id=document_id)
        motif = request.POST.get('motif', 'Document non conforme')
        
        if not motif:
            return JsonResponse({
                'success': False,
                'message': 'Veuillez fournir un motif de refus.'
            })
        
        # Utiliser la méthode existante du modèle Document
        document.refuser(request.user, motif)
        
        # Récupérer le propriétaire pour la notification
        proprietaire = document.get_proprietaire()
        
        # Notification au propriétaire
        if proprietaire:
            if hasattr(proprietaire, 'email'):  # C'est un utilisateur
                Notification.objects.create(
                    utilisateur=proprietaire,
                    titre="❌ Document rejeté",
                    contenu=f"Votre document '{document.nom}' a été rejeté. Motif : {motif}",
                    type='REFUS_DOCUMENT',
                    important=True
                )
            elif hasattr(proprietaire, 'promoteur'):  # C'est un projet
                Notification.objects.create(
                    utilisateur=proprietaire.promoteur,
                    titre="❌ Document rejeté",
                    contenu=f"Votre document '{document.nom}' a été rejeté. Motif : {motif}",
                    type='REFUS_DOCUMENT',
                    important=True
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Le document "{document.nom}" a été rejeté.',
            'document_id': document.id,
            'nouveau_statut': document.get_statut_display()
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du refus: {str(e)}'
        }, status=500)

# =============================================================================
# LISTE INVESTISSEURS PROJET
# =============================================================================

@login_required
def admin_liste_investisseurs(request, project_id):
    """Liste des investisseurs d'un projet (admin)"""
    if not request.user.est_administrateur():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('core:dashboard')
    
    projet = get_object_or_404(Projet, id=project_id)
    
    # Récupérer les investissements du projet
    investissements = Investissement.objects.filter(
        projet=projet,
        statut='CONFIRME'
    ).select_related('investisseur').order_by('-date_investissement')
    
    # Statistiques
    stats = {
        'total_investisseurs': investissements.values('investisseur').distinct().count(),
        'total_montant': investissements.aggregate(total=Sum('montant'))['total'] or 0,
        'moyenne_investissement': investissements.aggregate(moyenne=Avg('montant'))['moyenne'] or 0,
    }
    
    # Groupement par investisseur
    investissements_par_investisseur = {}
    for investissement in investissements:
        investisseur = investissement.investisseur
        if investisseur.id not in investissements_par_investisseur:
            investissements_par_investisseur[investisseur.id] = {
                'investisseur': investisseur,
                'montant_total': 0,
                'nombre_investissements': 0,
                'premier_investissement': investissement.date_investissement,
                'dernier_investissement': investissement.date_investissement,
            }
        
        invest_data = investissements_par_investisseur[investisseur.id]
        invest_data['montant_total'] += investissement.montant
        invest_data['nombre_investissements'] += 1
        
        if investissement.date_investissement < invest_data['premier_investissement']:
            invest_data['premier_investissement'] = investissement.date_investissement
        
        if investissement.date_investissement > invest_data['dernier_investissement']:
            invest_data['dernier_investissement'] = investissement.date_investissement
    
    # Convertir en liste et trier par montant total
    investisseurs_liste = list(investissements_par_investisseur.values())
    investisseurs_liste.sort(key=lambda x: x['montant_total'], reverse=True)
    
    context = {
        'projet': projet,
        'investisseurs': investisseurs_liste,
        'stats': stats,
        'total_investissements': investissements.count(),
    }
    
    return render(request, 'admin/projets/investisseurs.html', context)  

# =============================================================================
# PROFIL PROMOTEUR (ADMIN)
# =============================================================================

@login_required
def admin_profil_promoteur(request, promoteur_id):
    """Profil d'un promoteur (admin)"""
    if not request.user.est_administrateur():
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('core:dashboard')
    
    promoteur = get_object_or_404(Utilisateur, id=promoteur_id, est_promoteur=True)
    
    # Statistiques du promoteur
    projets = promoteur.projets.all()
    
    stats = {
        'total_projets': projets.count(),
        'projets_termines': projets.filter(statut='TERMINE').count(),
        'projets_en_cours': projets.filter(statut='EN_COURS_EXECUTION').count(),
        'projets_en_campagne': projets.filter(statut='EN_CAMPAGNE').count(),
        'projets_attente': projets.filter(statut='EN_ATTENTE_VALIDATION').count(),
        'projets_refuses': projets.filter(statut='REFUSE').count(),
        'montant_total_collecte': projets.aggregate(total=Sum('montant_collecte'))['total'] or 0,
        'montant_total_cible': projets.aggregate(total=Sum('montant_total'))['total'] or 0,
    }
    
    if stats['montant_total_cible'] > 0:
        stats['taux_reussite_moyen'] = round((stats['montant_total_collecte'] / stats['montant_total_cible']) * 100, 1)
    else:
        stats['taux_reussite_moyen'] = 0
    
    # Derniers projets
    projets_recents = projets.order_by('-date_creation')[:10]
    
    # Derniers comptes rendus
    comptes_rendus_recents = CompteRendu.objects.filter(
        projet__promoteur=promoteur
    ).order_by('-date_creation')[:5]
    
    # Documents du promoteur
    documents = Document.get_documents_utilisateur(promoteur.id)
    
    context = {
        'promoteur': promoteur,
        'stats': stats,
        'projets_recents': projets_recents,
        'comptes_rendus_recents': comptes_rendus_recents,
        'documents': documents,
        'documents_count': documents.count(),
    }
    
    return render(request, 'admin/promoteurs/profil.html', context)

# =============================================================================
# FONCTIONNALITÉS SUPPLÉMENTAIRES
# =============================================================================

@login_required
@require_http_methods(["POST"])
def admin_demander_modification_compte_rendu(request, cr_id):
    """Demander des modifications sur un compte rendu"""
    if not request.user.est_administrateur():
        return JsonResponse({
            'success': False,
            'message': 'Accès réservé aux administrateurs.'
        }, status=403)
    
    try:
        compte_rendu = get_object_or_404(CompteRendu, id=cr_id)
        commentaires = request.POST.get('commentaires', '').strip()
        
        # Validation des commentaires
        if not commentaires:
            return JsonResponse({
                'success': False,
                'message': 'Veuillez fournir des commentaires pour la modification.'
            })
        
        if len(commentaires) < 20:
            return JsonResponse({
                'success': False,
                'message': 'Les commentaires doivent contenir au moins 20 caractères.'
            })
        
        # Vérifier que le compte rendu est en attente
        if compte_rendu.statut != 'EN_ATTENTE_VALIDATION':
            return JsonResponse({
                'success': False,
                'message': f'Ce compte rendu n\'est plus en attente (statut: {compte_rendu.get_statut_display()})'
            })
        
        # Créer une demande de modification
        from apps.projects.models import DemandeModificationCompteRendu
        
        demande = DemandeModificationCompteRendu.objects.create(
            compte_rendu=compte_rendu,
            administrateur=request.user,
            commentaires=commentaires,
            date_demande=timezone.now()
        )
        
        # Mettre à jour le statut du compte rendu
        compte_rendu.statut = 'A_MODIFIER'
        compte_rendu.save()
        
        # Envoyer une notification au promoteur
        Notification.objects.create(
            utilisateur=compte_rendu.projet.promoteur,
            titre="📝 Modifications demandées",
            contenu=f"Des modifications sont demandées sur votre compte rendu '{compte_rendu.titre}'. Commentaires : {commentaires}",
            type='DEMANDE_MODIFICATION_COMPTE_RENDU',
            important=True,
            lien=reverse('projects:promoteur_compte_rendu')
        )
        
        messages.info(request, f"📝 Demande de modifications envoyée au promoteur.")
        
        return JsonResponse({
            'success': True,
            'message': f'La demande de modifications a été envoyée.',
            'nouveau_statut': 'À modifier',
            'statut_color': 'warning',
            'redirect_url': reverse('admin_perso:liste_comptes_rendus') 
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la demande de modifications: {str(e)}'
        }, status=500)