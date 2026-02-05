"""
Vues pour le module investments
Plateforme crowdBuilding - Burkina Faso
"""
import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from apps.accounts.models import Utilisateur
from apps.projects.models import Projet
from apps.notifications.models import Notification
from .models import Investissement, Transaction, StatutInvestissement, TypeTransaction, StatutTransaction
from django.utils import timezone
from django.db.models import Sum

from django.db import transaction



@login_required
def investir_projet(request, project_id):
    projet = get_object_or_404(Projet, id=project_id)
    valeur_part = Decimal(projet.valeur_part)

    if request.method == 'POST':
        # 🔹 Nombre de parts
        nombre_parts = request.POST.get('nombre_parts')
        if not nombre_parts:
            messages.error(request, "Veuillez saisir le nombre de parts.")
            return redirect('investments:investir', project_id=project_id)

        try:
            nombre_parts = int(nombre_parts)
        except (TypeError, ValueError):
            messages.error(request, "Nombre de parts invalide.")
            return redirect('investments:investir', project_id=project_id)

        # 🔒 RÈGLE MÉTIER : minimum défini par le promoteur
        nombre_min_parts = projet.nombre_min_parts or 1

        if nombre_parts < nombre_min_parts:
            messages.error(
                request,
                f"Vous devez investir au minimum {nombre_min_parts} parts pour ce projet."
            )
            return redirect('investments:investir', project_id=project_id)

        # 🔹 Vérification des parts disponibles
        parts_restantes = projet.nombre_total_parts - projet.parts_vendues
        if nombre_parts > parts_restantes:
            messages.error(
                request,
                f"Seulement {parts_restantes} parts restantes disponibles."
            )
            return redirect('investments:investir', project_id=project_id)

        # 🔹 Calcul du montant
        montant = Decimal(nombre_parts) * valeur_part

        # 🔹 Autres champs
        mode_paiement = request.POST.get('mode_paiement')
        origine_fonds = request.POST.get('origine_fonds')
        contrat_accepte = request.POST.get('contrat_accepte') == 'on'

        if not mode_paiement or not origine_fonds or not contrat_accepte:
            messages.error(
                request,
                "Veuillez remplir tous les champs et accepter le contrat."
            )
            return redirect('investments:investir', project_id=project_id)

        # 🔒 Transaction atomique pour éviter les doublons
        with transaction.atomic():
            investissement_existant = Investissement.objects.filter(
                investisseur=request.user,
                projet=projet
            ).first()

            if investissement_existant:
                total_parts_apres = investissement_existant.nombre_parts + nombre_parts
            else:
                total_parts_apres = nombre_parts

            if total_parts_apres < nombre_min_parts:
                messages.error(
                    request,
                    f"Le minimum requis pour ce projet est {nombre_min_parts} parts "
                    f"(vous en auriez {total_parts_apres})."
                )
                return redirect('investments:investir', project_id=project_id)

            # 🔹 Vérifier si l'investisseur a déjà un investissement pour ce projet
            investissement, created = Investissement.objects.get_or_create(
                investisseur=request.user,
                projet=projet,
                defaults={
                    'montant': montant,
                    'nombre_parts': nombre_parts,  # ✅ On ajoute le nombre de parts ici
                    'origine_fonds': origine_fonds,
                    'contrat_accepte': contrat_accepte,
                    'date_investissement': timezone.now(),
                }
            )

            if not created:
                # ➕ Ajouter les nouvelles parts à l'investissement existant
                investissement.montant += montant
                investissement.nombre_parts += nombre_parts  # ✅ MAJ nombre_parts
                investissement.date_investissement = timezone.now()
                investissement.save()

            # 🔹 Création de la transaction associée
            Transaction.objects.create(
                investissement=investissement,
                montant=montant,
                type=TypeTransaction.INVESTISSEMENT,
                statut=StatutTransaction.EN_ATTENTE,
                mode_paiement=mode_paiement,
                description=f"Ajout de {nombre_parts} parts dans le projet '{projet.titre}'"
            )

        messages.success(
            request,
            f"Votre investissement de {nombre_parts} part{'s' if nombre_parts>1 else ''} a été enregistré avec succès !"
        )
        return redirect(
            'investments:confirmation',
            investment_id=investissement.id
        )
    
    investissement = Investissement.objects.filter(
        investisseur=request.user,
        projet=projet
    ).first()  # None si pas encore créé

    # 🔹 GET
    return render(request, 'investments/investir.html', {
        'projet': projet,
        'valeur_part': valeur_part,
        'investisseurs_count': projet.investissements.count(),
        'investissement': investissement,  # 🔹 important pour le bouton de paiement
    })




@login_required
def confirmation_investissement(request, investment_id):
    """
    Étape 2 : Page de confirmation de l'investissement
    """
    investissement = get_object_or_404(Investissement, id=investment_id, investisseur=request.user)
    
    context = {
        'investissement': investissement,
        'projet': investissement.projet,
    }
    
    return render(request, 'investments/confirmation.html', context)


@login_required
def mes_investissements(request):
    """
    Page des investissements de l'utilisateur
    """
    investissements = request.user.investissements.all().order_by('-date_investissement')
    
    # Calculer les statistiques
    total_investi = sum(inv.montant for inv in investissements if inv.statut == StatutInvestissement.CONFIRME)
    nombre_projets = investissements.values('projet').distinct().count()
    
    context = {
        'investissements': investissements,
        'total_investi': total_investi,
        'nombre_projets': nombre_projets,
    }
    
    return render(request, 'investments/mes_investissements.html', context)


def list_investments(request):
    """Liste des investissements (pour les administrateurs)"""
    investments = Investissement.objects.all()
    return render(request, 'investments/list.html', {'investments': investments})

@login_required
def create_investment(request, project_id):
    """Créer un investissement"""
    if request.method == 'POST':
        # Logique de création de l'investissement
        messages.success(request, 'Investissement créé avec succès !')
        return redirect('investments:mes_investissements')
    return render(request, 'investments/create.html', {'project_id': project_id})


# apps/investments/views.py - Mettre à jour la vue detail_investissement

@login_required
def detail_investissement(request, investment_id):
    """Détail d'un investissement avec suivi du projet"""
    investment = get_object_or_404(Investissement, id=investment_id, investisseur=request.user)
    projet = investment.projet
    
    # Récupérer les étapes du projet (si elles existent)
    etapes = projet.etapes.all().order_by('ordre')
    
    # Calculer l'avancement global du projet
    avancement_global = 0
    if etapes.exists():
        etapes_terminees = etapes.filter(terminee=True).count()
        avancement_global = (etapes_terminees / etapes.count()) * 100
    
    # Récupérer les comptes rendus validés (uniquement ceux publiés)
    comptes_rendus_valides = projet.comptes_rendus.filter(
        statut='VALIDE',
        date_publication__lte=timezone.now()
    ).select_related('etape', 'administrateur_validateur').prefetch_related('images').order_by('-date_creation')
    
    context = {
        'investment': investment,
        'projet': projet,
        'etapes': etapes,
        'avancement_global': avancement_global,
        'comptes_rendus_valides': comptes_rendus_valides,
    }
    
    return render(request, 'investments/detail_investissement.html', context)


@login_required
def dashboard_investisseur(request):
    """
    Tableau de bord spécifique pour l'investisseur
    """
    user = request.user
    
    # Vérifier que l'utilisateur est un investisseur
    if not user.est_investisseur():
        messages.error(request, "Accès réservé aux investisseurs.")
        return redirect('core:dashboard')
    
    # Vérifier si le rôle est en attente de validation
    role_actif = user.get_role_actif()
    if role_actif and role_actif.statut == 'EN_ATTENTE_VALIDATION':
        return redirect('core:dashboard')
    
    # Investissements confirmés
    investissements = Investissement.objects.filter(
        investisseur=user,
        statut='CONFIRME'
    ).select_related('projet')
    
    # Statistiques
    stats_investissements = {
        'total': investissements.count(),
        'montant_total': investissements.aggregate(total=Sum('montant'))['total'] or Decimal('0'),
    }
    
    # Projets investis
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
    
    # Investissements récents (limite à 10)
    investissements_recents = investissements.order_by('-date_investissement')[:10]
    
    # 🔥 CORRECTION : Notifications récentes (TOUTES les notifications)
    from apps.notifications.models import Notification
    # Récupérer TOUTES les notifications de l'utilisateur
    notifications_all = Notification.objects.filter(
        utilisateur=user
    ).order_by('-date_creation')
    
    # Notifications récentes (limitées à 5)
    notifications_recentes = notifications_all[:5]
    
    # Compter les non-lues dans le queryset complet
    notifications_unread = notifications_all.filter(lue=False).count()
    
    context = {
        'user': user,
        'stats_investissements': stats_investissements,
        'projets_investis': projets_investis,
        'projets_en_cours': projets_en_cours,
        'projets_termines': projets_termines,
        'investissements_recents': investissements_recents,
        'notifications': notifications_recentes,  # 🔥 Toutes les notifications
        'notifications_unread': notifications_unread,  # 🔥 Toutes les non-lues
        'aujourdhui': timezone.now().date(),
    }
    
    return render(request, 'investments/dashboard_investisseur.html', context)