"""
Vues pour le module projects
Plateforme crowdBuilding - Burkina Faso
"""
from datetime import timedelta
import datetime
import json
from django.forms import ValidationError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from apps.accounts import models as accounts_models
from .forms import CompteRenduForm, CompteRenduModificationForm, ImageCompteRenduFormSet, NouveauProjetForm
from .models import CompteRendu, Projet, Etape, DocumentObligatoire, StatutProjet
from .utils import add_months
from apps.notifications.models import Notification
from apps.documents.models import Document, StatutDocument

# =============================================
# VUES PUBLIQUES
# =============================================

def list_projects(request):
    """Liste des projets publics"""
    projects = Projet.objects.filter(
        statut__in=[
            StatutProjet.EN_CAMPAGNE,
            StatutProjet.FINANCE,
            StatutProjet.EN_COURS_EXECUTION,
            StatutProjet.TERMINE
        ]
    ).select_related('promoteur').prefetch_related('images').order_by('-date_creation')
    
    # Appliquer les filtres
    search_query = request.GET.get('search', '')
    categorie_filter = request.GET.get('categorie', '')
    statut_filter = request.GET.get('statut', '')
    
    if search_query:
        projects = projects.filter(
            Q(titre__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(localisation__icontains=search_query)
        )
    
    if categorie_filter:
        projects = projects.filter(categorie=categorie_filter)
    
    if statut_filter:
        projects = projects.filter(statut=statut_filter)
    
    context = {
        'projects': projects,
        'search_query': search_query,
        'categorie_filter': categorie_filter,
        'statut_filter': statut_filter,
        'est_investisseur': request.user.is_authenticated and request.user.est_investisseur(),
    }
    
    return render(request, 'projects/list.html', context)


def project_detail(request, project_id):
    """Détail d'un projet - Version différente selon l'utilisateur"""
    project = get_object_or_404(
        Projet.objects.select_related('promoteur')
        .prefetch_related('images', 'documents', 'etapes', 'comptes_rendus'),
        id=project_id
    )
    
    # Vérifier que l'utilisateur peut voir le projet
    statuts_visibles = [
        StatutProjet.VALIDE,
        StatutProjet.EN_CAMPAGNE,
        StatutProjet.FINANCE,
        StatutProjet.EN_COURS_EXECUTION,
        StatutProjet.TERMINE
    ]
    
    if project.statut not in statuts_visibles:
        if not request.user.is_authenticated or (request.user != project.promoteur and not request.user.est_administrateur()):
            messages.error(request, "Vous n'avez pas accès à ce projet.")
            return redirect('projects:list')
    
    # Déterminer le template à utiliser
    is_admin = request.user.is_authenticated and request.user.est_administrateur()
    is_promoteur = request.user.is_authenticated and request.user == project.promoteur
    
    if is_admin:
        template_name = 'projects/detail.html'
        
        # Calculer des statistiques supplémentaires pour l'admin
        try:
            from apps.investments.models import Investissement
            investissements = Investissement.objects.filter(projet=project)
            nombre_investisseurs = investissements.values('investisseur').distinct().count()
        except:
            nombre_investisseurs = 0
            
        # Récupérer les comptes rendus
        comptes_rendus = CompteRendu.objects.filter(projet=project).order_by('-date_publication')[:5]
        
        # Statistiques du promoteur
        total_projets_promoteur = Projet.objects.filter(promoteur=project.promoteur).count()
        projets_termines_promoteur = Projet.objects.filter(
            promoteur=project.promoteur,
            statut='TERMINE'
        ).count()
        
        context = {
            'project': project,
            'taux_financement': project.taux_financement,
            'jours_restants': max(0, project.jours_restants),
            'est_promoteur': is_promoteur,
            'est_administrateur': is_admin,
            'est_investisseur': request.user.is_authenticated and request.user.est_investisseur(),
            'nombre_investisseurs': nombre_investisseurs,
            'comptes_rendus': comptes_rendus,
            'total_projets_promoteur': total_projets_promoteur,
            'projets_termines_promoteur': projets_termines_promoteur,
        }
        
    else:
        template_name = 'projects/public_detail.html'
        
        # Calculer des statistiques pour le template
        taux_financement = (project.montant_collecte / project.montant_total * 100) if project.montant_total > 0 else 0
        jours_restants = (project.date_fin - timezone.now().date()).days if project.date_fin else 0
        
        context = {
            'project': project,
            'taux_financement': taux_financement,
            'jours_restants': max(0, jours_restants),
            'est_promoteur': is_promoteur,
            'est_administrateur': is_admin,
            'est_investisseur': request.user.is_authenticated and request.user.est_investisseur(),
        }
    
    return render(request, template_name, context)



# =============================================
# VUES PROMOTEUR
# =============================================

@login_required
def dashboard_promoteur(request):
    """Dashboard promoteur"""
    if not request.user.est_promoteur() or not request.user.est_valide():
        messages.error(request, "Accès réservé aux promoteurs validés.")
        return redirect('core:dashboard')
    
    user = request.user
    projets = user.projets.all()
    
    stats = {
        'projets_actifs': projets.filter(
            statut__in=['EN_CAMPAGNE', 'FINANCE', 'EN_COURS_EXECUTION']
        ).count(),
        'montant_collecte': projets.aggregate(total=Sum('montant_collecte'))['total'] or 0,
        'en_attente_validation': projets.filter(statut='EN_ATTENTE_VALIDATION').count(),
        'projets_termines': projets.filter(statut='TERMINE').count(),
    }
    
    projets_recents = projets.order_by('-date_creation')[:5]
    projets_attention = []
    
    trois_jours = timezone.now() - timezone.timedelta(days=3)
    projets_attente_longue = projets.filter(
        statut='EN_ATTENTE_VALIDATION',
        date_creation__lt=trois_jours
    )
    
    for projet in projets_attente_longue:
        projets_attention.append({
            'id': projet.id,
            'titre': projet.titre,
            'raison_attention': 'En attente de validation depuis plus de 3 jours'
        })
    
    projets_en_campagne = projets.filter(statut='EN_CAMPAGNE')
    for projet in projets_en_campagne:
        taux_financement = projet.taux_financement
        if taux_financement < 30:
            projets_attention.append({
                'id': projet.id,
                'titre': projet.titre,
                'raison_attention': f'Financement faible ({taux_financement:.1f}%)'
            })
    
    activites_recentes = []
    
    dernier_valide = projets.filter(statut='VALIDE').order_by('-date_validation').first()
    if dernier_valide:
        activites_recentes.append({
            'titre': 'Projet validé',
            'description': f'{dernier_valide.titre} a été approuvé',
            'date': 'Récemment',
            'icon': 'ri-check-line',
            'color': 'success'
        })
    
    dernier_cr = CompteRendu.objects.filter(projet__promoteur=user).order_by('-date_publication').first()
    if dernier_cr:
        activites_recentes.append({
            'titre': 'Nouveau compte rendu',
            'description': f'Publié pour {dernier_cr.projet.titre}',
            'date': 'Récemment',
            'icon': 'ri-file-text-line',
            'color': 'primary'
        })
    
    projet_finance = projets.filter(statut='FINANCE').order_by('-date_creation').first()
    if projet_finance:
        activites_recentes.append({
            'titre': 'Objectif atteint',
            'description': f'{projet_finance.titre} financé à {projet_finance.taux_financement:.1f}%',
            'date': 'Récemment',
            'icon': 'ri-money-euro-circle-line',
            'color': 'warning'
        })
    
    nouveau_projet = projets.order_by('-date_creation').first()
    if nouveau_projet:
        activites_recentes.append({
            'titre': 'Nouveau projet créé',
            'description': f'{nouveau_projet.titre} a été créé',
            'date': 'Récemment',
            'icon': 'ri-add-circle-line',
            'color': 'info'
        })
    
    context = {
        'stats': stats,
        'projets_recents': projets_recents,
        'activites_recentes': activites_recentes[:4],
        'projets_attention': projets_attention[:3]
    }
    return render(request, 'promoteur/dashboard.html', context)


@login_required
def mes_projets_promoteur(request):
    """Page mes projets avec le nouveau design"""
    if not request.user.est_promoteur() or not request.user.est_valide():
        messages.error(request, "Accès réservé aux promoteurs validés.")
        return redirect('core:dashboard')
    
    projets = request.user.projets.all().order_by('-date_creation')
    
    statut_filter = request.GET.get('statut')
    if statut_filter:
        projets = projets.filter(statut=statut_filter)
    
    search_query = request.GET.get('search')
    if search_query:
        projets = projets.filter(
            Q(titre__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    context = {
        'projets': projets,
        'statuts': StatutProjet.choices,
    }
    
    return render(request, 'promoteur/projets.html', context)


@login_required
def nouveau_projet_promoteur(request):
    """Étape 1 : Formulaire principal du projet"""
    if not request.user.est_promoteur() or not request.user.est_valide():
        messages.error(request, "Accès réservé aux promoteurs validés.")
        return redirect('core:dashboard')
    
    projet_id = request.GET.get('projet_id')
    projet = None
    
    if projet_id:
        try:
            projet = get_object_or_404(Projet, id=projet_id, promoteur=request.user)
            if projet.statut not in [StatutProjet.BROUILLON, StatutProjet.A_COMPLETER]:
                messages.error(request, "Ce projet ne peut plus être modifié.")
                return redirect('projects:promoteur_projets')
        except:
            projet = None
    
    if request.method == 'POST':
        print("DEBUG - POST reçu pour projet_id:", projet_id)
        if projet:
            form = NouveauProjetForm(request.POST, request.FILES, instance=projet)
        else:
            form = NouveauProjetForm(request.POST, request.FILES)
        
        print("DEBUG - Form instancié, is_valid:", form.is_valid())
        print("DEBUG - Form errors:", form.errors)
        if form.is_valid():
            try:
                with transaction.atomic():
                    projet = form.save(commit=False)
                    
                    if not projet.id:
                        print('Nouveau projet, mode modification')
                        projet.promoteur = request.user
                        projet.statut = StatutProjet.BROUILLON
                    
                    if projet.date_debut and form.cleaned_data.get('duree'):
                        print("Calcul date_fin")
                        projet.date_fin = add_months(projet.date_debut, form.cleaned_data['duree'])
                    
                    description = form.cleaned_data['description']
                    print(f"Description length: {len(description)}")
                    if len(description) > 200:
                        projet.resume = description[:200] + "..."
                    else:
                        projet.resume = description
                    
                    print('Sauvegarde du projet')
                    projet.save()
                    
                    if not projet.id:
                        print('Erreur : le projet n\'a pas été sauvegardé correctement.')
                        sauvegarder_documents_obligatoires(projet, form.cleaned_data)
                    
                    definir_etapes = form.cleaned_data.get('definir_etapes_maintenant', False)
                    
                    if definir_etapes:
                        messages.success(request, 'Projet sauvegardé. Vous pouvez maintenant définir les étapes.')
                        return redirect('projects:promoteur_nouveau_projet_etapes', projet_id=projet.id)
                    else:
                        messages.success(request, 'Projet sauvegardé. Vérifiez les informations avant soumission.')
                        return redirect('projects:promoteur_confirmation_projet', projet_id=projet.id)
                        
            except Exception as e:
                messages.error(request, f'Erreur lors de la sauvegarde : {str(e)}')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    
    if projet:
        form = NouveauProjetForm(instance=projet)
    else:
        form = NouveauProjetForm()
    
    return render(request, 'promoteur/nouveau_projet.html', {
        'form': form,
        'projet': projet,
        'est_modification': projet is not None
    })


def sauvegarder_documents_obligatoires(projet, cleaned_data):
    """Sauvegarde les documents obligatoires"""
    documents_data = [
        ('PERMIS_CONSTRUIRE', cleaned_data['document_foncier'], 'Document foncier - Titre de propriété'),
        ('TECHNIQUE', cleaned_data['document_technique'], 'Document technique - Permis de construire'),
        ('BUSINESS_PLAN', cleaned_data['document_financier'], 'Document financier - Budget global'),
    ]
    
    for doc_type, fichier, nom in documents_data:
        if fichier:
            DocumentObligatoire.objects.create(
                projet=projet,
                type_document=doc_type,
                nom=nom,
                fichier=fichier,
                est_obligatoire=True,
                description=f"Document soumis lors de la création du projet"
            )


@login_required
def confirmation_projet(request, projet_id):
    """Page de confirmation avant soumission finale"""
    projet = get_object_or_404(Projet, id=projet_id, promoteur=request.user)
    
    if projet.statut not in [StatutProjet.BROUILLON, StatutProjet.A_COMPLETER]:
        messages.error(request, f"Ce projet a déjà le statut: {projet.get_statut_display()}")
        return redirect('projects:promoteur_projets')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'modifier_etapes':
            return redirect('projects:promoteur_nouveau_projet_etapes', projet_id=projet.id)
        
        elif action == 'modifier_projet':
            return redirect(f"{reverse('projects:promoteur_nouveau_projet')}?projet_id={projet.id}")
        
        elif action == 'confirmer':
            try:
                with transaction.atomic():
                    projet.statut = StatutProjet.EN_ATTENTE_VALIDATION
                    projet.save()
                    
                    try:
                        envoyer_notification_administration(projet)
                    except Exception as e:
                        print(f"DEBUG - Erreur notification: {e}")
                    
                    messages.success(request, 'Projet soumis avec succès ! Il sera examiné sous 48-72h.')
                    return redirect('projects:promoteur_projets')
                    
            except Exception as e:
                messages.error(request, f'Erreur lors de la soumission: {str(e)}')
    
    etapes = projet.etapes.all().order_by('ordre')
    
    context = {
        'projet': projet,
        'etapes': etapes,
        'has_etapes': etapes.exists()
    }
    
    return render(request, 'promoteur/confirmation_projet.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from datetime import date
from django.utils.dateparse import parse_date
from .models import Projet, Etape

@login_required
def nouveau_projet_etapes(request, projet_id):
    """Étape 2/2 : Définition des étapes du projet"""
    projet = get_object_or_404(Projet, id=projet_id, promoteur=request.user)

    # On considère un projet comme "nouveau" si ses étapes ne sont pas encore définies
    est_nouveau_projet = not projet.etapes_definies

    if request.method == 'POST':

        # Cas : pas d’étapes
        if request.POST.get('pas_d_etapes') == '1':
            projet.etapes_definies = False
            projet.save()
            return redirect(
                'projects:promoteur_confirmation_projet',
                projet_id=projet.id
            )

        erreurs = False
        etapes_a_creer = []

        index = 0
        while True:
            titre = request.POST.get(f'etape_titre_{index}')
            if titre is None:
                break  # plus d'étapes envoyées

            titre = titre.strip()
            description = request.POST.get(f'etape_description_{index}', '').strip()
            date_debut_str = request.POST.get(f'etape_date_debut_{index}')
            duree_str = request.POST.get(f'etape_duree_{index}')
            ordre_str = request.POST.get(f'etape_ordre_{index}')

            # Étape totalement vide → ignorée
            if not titre and not date_debut_str and not duree_str:
                index += 1
                continue

            # Étape partiellement remplie → erreur
            if not titre or not date_debut_str or not duree_str:
                messages.error(
                    request,
                    f"Étape {index + 1} : tous les champs obligatoires doivent être renseignés."
                )
                erreurs = True
                index += 1
                continue

            # Validation date
            date_debut = parse_date(date_debut_str)
            if not date_debut or date_debut <= date.today():
                messages.error(
                    request,
                    f"Étape {index + 1} : la date de début doit être postérieure à aujourd’hui."
                )
                erreurs = True
                index += 1
                continue

            # Validation durée
            try:
                duree = int(duree_str)
                if duree <= 0:
                    raise ValueError
            except ValueError:
                messages.error(
                    request,
                    f"Étape {index + 1} : la durée doit être un nombre positif."
                )
                erreurs = True
                index += 1
                continue

            # Ordre
            try:
                ordre = int(ordre_str) if ordre_str else index + 1
            except ValueError:
                ordre = index + 1

            # Étape valide
            etapes_a_creer.append(
                Etape(
                    projet=projet,
                    titre=titre,
                    description=description,
                    date_debut=date_debut,
                    duree_estimee=duree,
                    ordre=ordre
                )
            )

            index += 1

        # Si erreurs, on revient sur le formulaire
        if erreurs:
            return redirect(
                'projects:promoteur_nouveau_projet_etapes',
                projet_id=projet.id
            )

        # Si aucune étape valide ET pas de "pas_d_etapes", on affiche l'erreur
        if not etapes_a_creer and request.POST.get('pas_d_etapes') != '1':
            messages.error(
                request,
                "Veuillez renseigner au moins une étape ou cocher « pas d’étapes »."
            )
            return redirect(
                'projects:promoteur_nouveau_projet_etapes',
                projet_id=projet.id
            )

        # Sauvegarde des étapes
        with transaction.atomic():
            projet.etapes.all().delete()
            Etape.objects.bulk_create(etapes_a_creer)
            projet.etapes_definies = True
            projet.save()

        messages.success(request, "Les étapes ont été enregistrées avec succès.")
        return redirect(
            'projects:promoteur_confirmation_projet',
            projet_id=projet.id
        )

    # GET
    etapes_existantes = projet.etapes.all().order_by('ordre') if not est_nouveau_projet else []
    return render(request, 'promoteur/etapes.html', {
        'projet': projet,
        'est_nouveau_projet': est_nouveau_projet,
        'etapes_existantes': etapes_existantes,
        'projet_selectionne': projet if not est_nouveau_projet else None,
    })




@login_required
def gestion_etapes(request, projet_id=None):
    """Gestion des étapes pour un projet existant"""
    projets = Projet.objects.filter(
        promoteur=request.user,
        statut__in=[
            StatutProjet.VALIDE,
            StatutProjet.EN_CAMPAGNE,
            StatutProjet.EN_COURS_EXECUTION,
            StatutProjet.FINANCE
        ]
    ).order_by('-date_creation')
    
    projet_selectionne = None
    etapes_existantes = []
    
    if request.method == 'POST':
        projet_id_post = request.POST.get('projet_id')
        if projet_id_post:
            try:
                projet_selectionne = get_object_or_404(Projet, id=projet_id_post, promoteur=request.user)
                
                if 'sauvegarder' in request.POST:
                    with transaction.atomic():
                        projet_selectionne.etapes.all().delete()
                        
                        nombre_etapes = int(request.POST.get('nombre_etapes', 0))
                        
                        for i in range(nombre_etapes):
                            titre = request.POST.get(f'etape_titre_{i}')
                            description = request.POST.get(f'etape_description_{i}', '')
                            ordre = request.POST.get(f'etape_ordre_{i}')
                            duree_mois = request.POST.get(f'etape_duree_{i}', '1')
                            date_debut = request.POST.get(f'etape_date_debut_{i}', '')
                            
                            if titre and duree_mois and date_debut and ordre:
                                try:
                                    duree_int = int(duree_mois)
                                    if duree_int < 1:
                                        duree_int = 1
                                except (ValueError, TypeError):
                                    duree_int = 1
                                
                                try:
                                    date_debut_obj = datetime.datetime.strptime(date_debut, '%Y-%m-%d').date()
                                except (ValueError, TypeError):
                                    date_debut_obj = timezone.now().date()
                                
                                Etape.objects.create(
                                    projet=projet_selectionne,
                                    titre=titre,
                                    description=description,
                                    ordre=int(ordre),
                                    duree_estimee=duree_int,
                                    date_debut=date_debut_obj
                                )
                        
                        projet_selectionne.etapes_definies = (nombre_etapes > 0)
                        projet_selectionne.save()
                        
                        messages.success(request, f'Étapes mises à jour pour le projet "{projet_selectionne.titre}" !')
                        return redirect('projects:promoteur_etapes')
                        
            except Exception as e:
                messages.error(request, f'Erreur lors de la mise à jour des étapes: {str(e)}')
    
    elif projet_id:
        projet_selectionne = get_object_or_404(Projet, id=projet_id, promoteur=request.user)
    
    if projet_selectionne:
        etapes_existantes = projet_selectionne.etapes.all().order_by('ordre')
    
    return render(request, 'promoteur/etapes.html', {
        'projets': projets,
        'projet_selectionne': projet_selectionne,
        'etapes_existantes': etapes_existantes,
        'est_nouveau_projet': False
    })


def envoyer_notification_administration(projet):
    """Envoie une notification aux administrateurs pour un nouveau projet"""
    from .utils import envoyer_notification_aux_administrateurs
    
    succes = envoyer_notification_aux_administrateurs(
        titre="🚀 Nouveau projet soumis",
        contenu=f"Le promoteur {projet.promoteur.nom_complet} a soumis un nouveau projet : '{projet.titre}'.",
        type_notif='NOUVEAU_PROJET',
        lien=projet.get_absolute_url() if hasattr(projet, 'get_absolute_url') else '#'
    )
    
    if not succes:
        print(f"📢 NOUVEAU PROJET (notifications échouées): {projet.titre} par {projet.promoteur.email}")


@login_required
def detail_projet_promoteur(request, project_id):
    """Détail d'un projet dans l'espace promoteur"""
    if not request.user.est_promoteur() or not request.user.est_valide():
        messages.error(request, "Accès réservé aux promoteurs validés.")
        return redirect('core:dashboard')
    
    try:
        projet = get_object_or_404(
            Projet.objects.select_related('promoteur')
            .prefetch_related('images', 'documents', 'etapes', 'comptes_rendus'),
            id=project_id,
            promoteur=request.user
        )
        
        # Récupérer les investissements
        try:
            from apps.investments.models import Investissement
            investissements = Investissement.objects.filter(projet=projet).select_related('investisseur')
            investisseurs_count = investissements.values('investisseur').distinct().count()
            total_investi = investissements.aggregate(total=Sum('montant'))['total'] or 0
        except:
            investissements = []
            investisseurs_count = 0
            total_investi = 0
        
        # Récupérer les étapes et comptes rendus
        etapes = projet.etapes.all().order_by('ordre')
        comptes_rendus = projet.comptes_rendus.all().order_by('-date_publication')
        
        etapes_terminees_count = etapes.filter(terminee=True).count()
        
        parts_vendues = projet.parts_vendues
        parts_restantes = projet.parts_restantes
        
        context = {
            'projet': projet,
            'etapes': etapes,
            'etapes_terminees_count': etapes_terminees_count,
            'comptes_rendus': comptes_rendus,
            'investissements': investissements,
            'investisseurs_count': investisseurs_count,
            'total_investi': total_investi,
            'parts_vendues': parts_vendues,
            'parts_restantes': parts_restantes,
        }
        
        return render(request, 'promoteur/projet_detail.html', context)
        
    except Exception as e:
        messages.error(request, f"Erreur lors du chargement du projet: {str(e)}")
        return redirect('projects:promoteur_projets')



# ============================================
# VUES PROMOTEUR
# ============================================

@login_required
def gestion_compte_rendu(request):
    """Page principale de gestion des comptes rendus"""
    if not request.user.est_promoteur():
        messages.error(request, "Accès réservé aux promoteurs.")
        return redirect('core:dashboard')
    
    # Récupérer les comptes rendus de l'utilisateur
    comptes_rendus = CompteRendu.objects.filter(
        projet__promoteur=request.user
    ).select_related('projet', 'etape').prefetch_related('images').order_by('-date_creation')
    
    # Statistiques
    stats = {
        'total': comptes_rendus.count(),
        'en_attente': comptes_rendus.filter(statut='EN_ATTENTE_VALIDATION').count(),
        'valides': comptes_rendus.filter(statut='VALIDE').count(),
        'rejetes': comptes_rendus.filter(statut='REJETE').count(),
    }
    
    context = {
        'comptes_rendus': comptes_rendus,
        'stats': stats,
        'active_tab': 'liste',
    }
    
    return render(request, 'promoteur/compte_rendu.html', context)

from django.shortcuts import get_object_or_404

@login_required
def nouveau_compte_rendu(request, projet_id=None):
    """Création d'un nouveau compte rendu - VERSION CORRIGÉE"""
    if not request.user.est_promoteur():
        messages.error(request, "Accès réservé aux promoteurs.")
        return redirect('core:dashboard')
    
    # Gestion du projet pré-sélectionné
    projet_initial = None
    if projet_id:
        try:
            projet_initial = Projet.objects.get(
                id=projet_id, 
                promoteur=request.user,
                statut__in=['EN_COURS_EXECUTION', 'FINANCE', 'EN_CAMPAGNE']
            )
        except Projet.DoesNotExist:
            messages.warning(request, "Projet non trouvé ou non accessible pour les comptes rendus.")
            return redirect('projects:promoteur_compte_rendu')
    
    if request.method == 'POST':
        form = CompteRenduForm(
            request.POST, 
            user=request.user,
            projet_pre_selectionne=projet_initial
        )
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    compte_rendu = form.save(commit=False)
                    compte_rendu.statut = 'EN_ATTENTE_VALIDATION'
                    compte_rendu.save()
                    
                    # Gestion des images avec le formset
                    image_formset = ImageCompteRenduFormSet(
                        request.POST,
                        request.FILES,
                        instance=compte_rendu,
                        prefix='images'
                    )
                    
                    if image_formset.is_valid():
                        images = image_formset.save()
                        
                        # Validation : au moins une image
                        if compte_rendu.images.count() == 0:
                            raise ValidationError("Au moins une image est requise.")
                        
                        # Validation : maximum 10 images
                        if compte_rendu.images.count() > 10:
                            raise ValidationError("Maximum 10 images autorisées.")
                        
                        # Soumettre le compte rendu (envoie automatiquement les notifications)
                        compte_rendu.soumettre()
                        
                        messages.success(
                            request,
                            f"✅ Compte rendu '{compte_rendu.titre}' soumis avec succès ! "
                            "Il sera examiné par l'administration dans les 48h."
                        )
                        
                        # Rediriger vers la gestion des comptes rendus
                        return redirect('projects:promoteur_compte_rendu')
                    else:
                        # Afficher les erreurs spécifiques du formset
                        error_messages = []
                        for form_img in image_formset:
                            if form_img.errors:
                                for field, errors in form_img.errors.items():
                                    for error in errors:
                                        error_messages.append(f"Image: {field} - {error}")
                        
                        if error_messages:
                            raise ValidationError("Erreurs dans les images : " + "; ".join(error_messages))
                        else:
                            raise ValidationError("Veuillez vérifier les images téléchargées.")
                            
            except ValidationError as e:
                messages.error(request, str(e))
                # Réinitialiser le formset pour conserver les images
                image_formset = ImageCompteRenduFormSet(
                    request.POST,
                    request.FILES,
                    prefix='images'
                )
            except Exception as e:
                messages.error(request, f"Erreur lors de la création : {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            # Afficher les erreurs du formulaire principal
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        # Initialisation des formulaires
        initial_data = {}
        if projet_initial:
            initial_data['projet'] = projet_initial
        
        form = CompteRenduForm(
            user=request.user, 
            initial=initial_data,
            projet_pre_selectionne=projet_initial
        )
        image_formset = ImageCompteRenduFormSet(prefix='images')
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'active_tab': 'nouveau',
        'projet_initial': projet_initial,
        'projets_disponibles': Projet.objects.filter(
            promoteur=request.user,
            statut__in=['EN_COURS_EXECUTION', 'FINANCE', 'EN_CAMPAGNE']
        ).order_by('-date_creation') if not projet_initial else []
    }
    
    return render(request, 'promoteur/compte_rendu.html', context)

@login_required
def modifier_compte_rendu(request, cr_id):
    """Modification d'un compte rendu existant"""
    if not request.user.est_promoteur():
        messages.error(request, "Accès réservé aux promoteurs.")
        return redirect('core:dashboard')
    
    compte_rendu = get_object_or_404(
        CompteRendu,
        id=cr_id,
        projet__promoteur=request.user
    )
    
    # Vérifier si le compte rendu peut être modifié
    if not compte_rendu.peut_modifier:
        messages.error(request, "Ce compte rendu ne peut plus être modifié.")
        return redirect('projects:promoteur_compte_rendu')
    
    if request.method == 'POST':
        form = CompteRenduModificationForm(
            request.POST,
            instance=compte_rendu,
            user=request.user
        )
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Mettre à jour le compte rendu
                    compte_rendu = form.save(commit=False)
                    
                    # Si c'était rejeté, repasser en attente
                    if compte_rendu.statut == 'REJETE':
                        compte_rendu.statut = 'EN_ATTENTE_VALIDATION'
                        compte_rendu.motif_rejet = ""
                    
                    compte_rendu.save()
                    
                    # Gérer les images
                    image_formset = ImageCompteRenduFormSet(
                        request.POST,
                        request.FILES,
                        instance=compte_rendu,
                        prefix='images'
                    )
                    
                    if image_formset.is_valid():
                        image_formset.save()
                        
                        # Vérifier qu'il reste au moins une image
                        if compte_rendu.images.count() == 0:
                            raise ValidationError("Au moins une image est requise.")
                        
                        # Soumettre à nouveau
                        compte_rendu.soumettre()
                        
                        messages.success(
                            request,
                            f"✅ Compte rendu '{compte_rendu.titre}' modifié et resoumis avec succès !"
                        )
                        
                        return redirect('projects:promoteur_compte_rendu')
                    else:
                        raise ValidationError("Erreur dans les images.")
                        
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Erreur lors de la modification : {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CompteRenduModificationForm(instance=compte_rendu, user=request.user)
    
    context = {
        'form': form,
        'compte_rendu': compte_rendu,
        'image_formset': ImageCompteRenduFormSet(instance=compte_rendu, prefix='images'),
        'active_tab': 'modifier',
        'est_modification': True,
    }
    
    return render(request, 'promoteur/nouveau_compte_rendu.html', context)

@login_required
def supprimer_compte_rendu(request, cr_id):
    """Suppression d'un compte rendu"""
    if not request.user.est_promoteur():
        messages.error(request, "Accès réservé aux promoteurs.")
        return redirect('core:dashboard')
    
    compte_rendu = get_object_or_404(
        CompteRendu,
        id=cr_id,
        projet__promoteur=request.user
    )
    
    # Vérifier si le compte rendu peut être supprimé
    if not compte_rendu.peut_modifier:
        messages.error(request, "Ce compte rendu ne peut plus être supprimé.")
        return redirect('projects:promoteur_compte_rendu')
    
    if request.method == 'POST':
        titre = compte_rendu.titre
        compte_rendu.delete()
        messages.success(request, f"✅ Le compte rendu '{titre}' a été supprimé.")
        return redirect('projects:promoteur_compte_rendu')
    
    return render(request, 'promoteur/confirmation_suppression.html', {
        'compte_rendu': compte_rendu,
        'type_objet': 'compte rendu',
    })

@login_required
def detail_compte_rendu_promoteur(request, cr_id):
    """Détail d'un compte rendu (vue promoteur)"""
    if not request.user.est_promoteur():
        messages.error(request, "Accès réservé aux promoteurs.")
        return redirect('core:dashboard')
    
    compte_rendu = get_object_or_404(
        CompteRendu.objects.select_related('projet', 'etape', 'administrateur_validateur')
                          .prefetch_related('images'),
        id=cr_id,
        projet__promoteur=request.user
    )
    
    context = {
        'compte_rendu': compte_rendu,
        'images': compte_rendu.images.all().order_by('ordre'),
        'peut_modifier': compte_rendu.peut_modifier,
    }
    
    return render(request, 'promoteur/detail_compte_rendu.html', context)

# ============================================
# VUES AJAX
# ============================================

@login_required
@require_http_methods(["GET"])
def ajax_get_etapes_projet(request):
    """Retourne les étapes d'un projet en AJAX"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Non authentifié'}, status=403)
    
    projet_id = request.GET.get('projet_id')
    
    if not projet_id:
        return JsonResponse({'error': 'ID projet manquant'}, status=400)
    
    try:
        # Vérifier que l'utilisateur a accès à ce projet
        projet = get_object_or_404(
            Projet, 
            id=projet_id, 
            promoteur=request.user
        )
        
        # Récupérer les étapes
        etapes = projet.etapes.all().order_by('ordre')
        
        etapes_data = [
            {
                'id': etape.id,
                'texte': f"{etape.ordre}. {etape.titre}",
                'description': etape.description[:100] + '...' if len(etape.description) > 100 else etape.description,
                'duree': etape.duree_estimee,
                'date_debut': etape.date_debut.strftime('%d/%m/%Y') if etape.date_debut else None,
            }
            for etape in etapes
        ]
        
        return JsonResponse({
            'success': True,
            'etapes': etapes_data,
            'count': len(etapes_data)
        })
        
    except Projet.DoesNotExist:
        return JsonResponse({'error': 'Projet non trouvé ou non autorisé'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def ajax_upload_image_temporaire(request):
    """Upload temporaire d'image pour prévisualisation"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Non authentifié'}, status=403)
    
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'Aucune image fournie'}, status=400)
    
    image_file = request.FILES['image']
    
    # Validation
    try:
        # Vérifier la taille (10MB max)
        if image_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'error': 'La taille du fichier ne doit pas dépasser 10MB.'
            }, status=400)
        
        # Vérifier le type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'error': 'Format non supporté. Formats acceptés: JPEG, PNG, WebP.'
            }, status=400)
        
        # Sauvegarder temporairement
        fs = FileSystemStorage(location='media/temp')
        filename = fs.save(f"temp_{request.user.id}_{image_file.name}", image_file)
        url = fs.url(filename)
        
        return JsonResponse({
            'success': True,
            'filename': filename,
            'url': url,
            'size': image_file.size,
            'name': image_file.name,
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
def visualiser_document(request, document_id):
    """Visualiser un document"""
    document = get_object_or_404(Document, id=document_id)
    
    # Vérifier les permissions
    if not (request.user.est_administrateur() or 
            (document.proprietaire_type == 'projet' and 
             request.user == document.get_proprietaire().promoteur)):
        return HttpResponseForbidden("Accès non autorisé.")
    
    return redirect(document.fichier.url)


@login_required
def telecharger_document(request, document_id):
    """Télécharger un document"""
    document = get_object_or_404(Document, id=document_id)
    
    # Vérifier les permissions
    if not (request.user.est_administrateur() or 
            (document.proprietaire_type == 'projet' and 
             request.user == document.get_proprietaire().promoteur)):
        return HttpResponseForbidden("Accès non autorisé.")
    
    response = FileResponse(document.fichier.open(), as_attachment=True)
    response['Content-Disposition'] = f'attachment; filename="{document.nom}{document.extension}"'
    return response


@login_required
def notifications_promoteur(request):
    notifications = Notification.objects.filter(
        utilisateur=request.user
    ).order_by('-date_creation')

    return render(request, 'promoteur/notifications.html', {
        'notifications': notifications
    })
