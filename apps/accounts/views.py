"""
Vues pour la gestion des utilisateurs et des rôles
Plateforme crowdBuilding - Burkina Faso
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count

from apps.documents import models
from apps.documents.models import Document

from .models import Utilisateur, Role
from .forms import InscriptionForm, ConnexionForm, ProfilForm, ChangementMotDePasseForm
from apps.notifications.models import Notification
from .models import Utilisateur, Role, TypeRole, StatutRole, StatutCompte
from apps.projects.models import StatutProjet  # Pour les constantes de statut
from django.db.models import Sum



class ConnexionView(LoginView):
    """
    Vue de connexion personnalisée CORRIGÉE
    """
    template_name = 'accounts/login.html'
    form_class = ConnexionForm
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirection après connexion réussie"""
        return reverse_lazy('core:dashboard')
    
    def form_valid(self, form):
        """Traitement du formulaire de connexion CORRIGÉ"""
        # Récupérer les données du formulaire
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')
        remember_me = form.cleaned_data.get('remember_me', False)
        
        # Authentifier l'utilisateur avec email comme username
        user = authenticate(self.request, username=email, password=password)
        
        if user is not None:
            login(self.request, user)
            
            # Gérer la session "Se souvenir de moi"
            if not remember_me:
                self.request.session.set_expiry(0)  # Session expire à la fermeture du navigateur
            else:
                self.request.session.set_expiry(1209600)  # 2 semaines
            
            messages.success(self.request, f'Bienvenue {user.prenom} !')
            return redirect(self.get_success_url())
        else:
            form.add_error(None, 'Email ou mot de passe incorrect.')
            return self.form_invalid(form)
    
    def get_form_kwargs(self):
        """Surcharger pour éviter de passer 'request' au formulaire"""
        kwargs = super().get_form_kwargs()
        # Ne pas passer 'request' au formulaire
        if 'request' in kwargs:
            del kwargs['request']
        return kwargs

class DeconnexionView(LogoutView):
    """
    Vue de déconnexion
    """
    next_page = reverse_lazy('core:home')
    
    def dispatch(self, request, *args, **kwargs):
        """Ajouter un message de déconnexion"""
        messages.info(request, 'Vous avez été déconnecté avec succès.')
        return super().dispatch(request, *args, **kwargs)


class InscriptionView(CreateView):
    model = Utilisateur
    form_class = InscriptionForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        """Traitement du formulaire d'inscription"""
        print("⭐ DÉBUT FORM_VALID - Le formulaire est valide!")
        try:
            with transaction.atomic():
                print("⭐ TRANSACTION DÉBUT")
                
                # Sauvegarder l'utilisateur et créer le rôle
                user = form.save()
                print(f"⭐ UTILISATEUR CRÉÉ: {user.email}")
                
                # CONNEXION AUTOMATIQUE
                from django.contrib.auth import login
                login(self.request, user)
                print("⭐ UTILISATEUR CONNECTÉ")
                
                # Notification
                Notification.objects.create(
                    utilisateur=user,
                    titre="Bienvenue sur crowdBuilding !",
                    contenu=f"Bonjour {user.prenom}, Votre compte est en attente de validation.",
                    type='VALIDATION_COMPTE'
                )
                print("⭐ NOTIFICATION CRÉÉE")
                
                messages.success(self.request, 'Compte créé avec succès !')
                print("⭐ REDIRECTION VERS DASHBOARD")
                
                return redirect('core:dashboard')
                
        except Exception as e:
            print(f"⭐ ERREUR dans form_valid: {e}")
            messages.error(self.request, f'Erreur: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        """Traitement du formulaire invalide"""
        print("⭐ FORM_INVALID - Le formulaire a des erreurs!")
        print(f"⭐ ERREURS DU FORMULAIRE: {form.errors}")
        print(f"⭐ DONNÉES DU FORMULAIRE: {form.cleaned_data}")
        
        messages.error(self.request, 'Veuillez corriger les erreurs ci-dessous.')
        return super().form_invalid(form)

@login_required
def profil(request):
    """
    Vue de consultation et modification du profil
    """
    # IMPORT TOUJOURS EN HAUT de la fonction
    from apps.documents.models import Document
    from apps.projects.models import Projet
    from apps.investments.models import Investissement
    from apps.notifications.models import Notification as NotifModel
    from django.db import models
    
    # LES SUPERUSERS ET ADMINISTRATEURS ONT TOUJOURS ACCÈS
    if not request.user.est_valide() and not request.user.est_administrateur():
        messages.warning(request, "Votre compte est en attente de validation. Vous ne pouvez pas accéder à votre profil pour le moment.")
        return redirect('core:dashboard')
    
    user = request.user
    role_actif = user.get_role_actif()
    
    # CONTEXTE DE BASE
    context = {
        'user': user,
        'role_actif': role_actif,
        'is_superuser': user.is_superuser,
        'is_administrateur': user.est_administrateur(),
    }
    
    # PROFIL DIFFÉRENT SELON LE RÔLE
    if user.est_administrateur():
        # ======================
        # PROFIL ADMINISTRATEUR
        # ======================
        all_documents = Document.objects.all()
        documents_attente = Document.get_documents_en_attente()
        
        # Statistiques globales pour l'admin
        stats = {
            'total_utilisateurs': Utilisateur.objects.count(),
            'utilisateurs_attente': Utilisateur.objects.filter(
                roles__statut='EN_ATTENTE_VALIDATION'
            ).distinct().count(),
            'total_projets': Projet.objects.count(),
            'projets_actifs': Projet.objects.filter(statut='ACTIF').count(),
            'total_investissements': Investissement.objects.count(),
            'documents_attente': documents_attente.count(),
            'investissements_total': Investissement.objects.aggregate(
                total=models.Sum('montant')
            )['total'] or 0,
        }
        
        context.update({
            'stats': stats,
            'all_documents': all_documents,
            'documents_count': all_documents.count(),
            'documents_attente': documents_attente,
            # CORRECTION : 'lu' → 'lue'
            'unread_notifications_count': NotifModel.objects.filter(lue=False).count(),
        })
        
    elif user.est_promoteur():
        # ======================
        # PROFIL PROMOTEUR
        # ======================
        user_documents = Document.get_documents_utilisateur(user.id)
        projets_utilisateur = user.projets.all()
        
        stats = {
            'total_projets': projets_utilisateur.count(),
            'projets_actifs': projets_utilisateur.filter(statut='ACTIF').count(),
            'projets_termines': projets_utilisateur.filter(statut='TERMINE').count(),
            'projets_attente': projets_utilisateur.filter(statut='EN_ATTENTE').count(),
            'montant_levé': projets_utilisateur.aggregate(
                total=models.Sum('montant_collecte')
            )['total'] or 0,
        }
        
        context.update({
            'stats': stats,
            'user_documents': user_documents,
            'user_documents_count': user_documents.count(),
            'projets': projets_utilisateur[:5],  # 5 derniers projets
            # CORRECTION : 'lu' → 'lue'
            'unread_notifications_count': NotifModel.objects.filter(utilisateur=user, lue=False).count(),
        })
        
    elif user.est_investisseur():
        # ======================
        # PROFIL INVESTISSEUR
        # ======================
        user_documents = Document.get_documents_utilisateur(user.id)
        investissements_utilisateur = user.investissements.filter(statut='CONFIRME')
        
        # CORRECTION : Calcul manuel du retour estimé avec Decimal
        from decimal import Decimal
        
        # Récupérer le montant total investi
        montant_total_investi = investissements_utilisateur.aggregate(
            total=models.Sum('montant')
        )['total']
        
        # Si aucun investissement, mettre à 0
        if montant_total_investi is None:
            montant_total_investi = Decimal('0')
        
        # CORRECTION : Utiliser Decimal pour le calcul du retour (10%)
        retour_estime = montant_total_investi * Decimal('0.10')
        
        stats = {
            'total_investissements': investissements_utilisateur.count(),
            'montant_investi': montant_total_investi,
            # CORRECTION : Utilisation du retour calculé avec Decimal
            'retour_attendu': retour_estime,
            'projets_investis': investissements_utilisateur.values('projet').distinct().count(),
            # Optionnel : Ajouter le retour annuel moyen
            'retour_moyen_annuel': Decimal('12.5'),  # En pourcentage
        }
        
        context.update({
            'stats': stats,
            'user_documents': user_documents,
            'user_documents_count': user_documents.count(),
            'investissements': investissements_utilisateur[:5],  # 5 derniers investissements
            'unread_notifications_count': NotifModel.objects.filter(utilisateur=user, lue=False).count(),
        })
            
    else:
        # ======================
        # PROFIL UTILISATEUR EN ATTENTE
        # ======================
        user_documents = Document.get_documents_utilisateur(user.id)
        
        stats = {
            'documents_uploades': user_documents.count(),
            'documents_valides': user_documents.filter(statut='VALIDE').count(),
            'documents_attente': user_documents.filter(statut='EN_ATTENTE').count(),
        }
        
        context.update({
            'stats': stats,
            'user_documents': user_documents,
            'user_documents_count': user_documents.count(),
            # CORRECTION : 'lu' → 'lue'
            'unread_notifications_count': NotifModel.objects.filter(utilisateur=user, lue=False).count(),
        })
    
    return render(request, 'accounts/profile.html', context)

@login_required
def modifier_profil(request):
    """
    Vue de modification du profil
    """
    if not request.user.est_valide:
        messages.warning(request, "Votre compte est en attente de validation.")
        return redirect('core:dashboard_attente')
        
    if request.method == 'POST':
        form = ProfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('accounts:profile')
    else:
        form = ProfilForm(instance=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/edit_profile.html', context)


@login_required
def changer_mot_de_passe(request):
    """
    Vue de changement de mot de passe
    """
    if request.method == 'POST':
        form = ChangementMotDePasseForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre mot de passe a été changé avec succès.')
            return redirect('accounts:profile')
    else:
        form = ChangementMotDePasseForm(request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/change_password.html', context)


@login_required
def basculer_role(request):
    """
    Vue pour basculer entre les rôles d'un utilisateur
    """
    user = request.user
    roles = user.roles.all()
    
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        try:
            role = roles.get(id=role_id)
            if role.statut == 'VALIDE':
                # Désactiver le rôle actuel
                user.roles.filter(role_actif=True).update(role_actif=False)
                # Activer le nouveau rôle
                role.role_actif = True
                role.save()
                
                messages.success(request, f'Vous utilisez maintenant le rôle {role.get_type_display()}.')
            else:
                messages.error(request, 'Ce rôle n\'est pas validé.')
        except Role.DoesNotExist:
            messages.error(request, 'Rôle invalide.')
        
        return redirect('core:dashboard')
    
    context = {
        'roles': roles,
    }
    
    return render(request, 'accounts/switch_role.html', context)


@login_required
def notifications(request):
    """
    Vue des notifications de l'utilisateur - NOUVELLE VERSION
    """
    user = request.user
    notifications_list = user.notifications.all().order_by('-date_creation')
    
    # Récupérer ou créer les paramètres de notification
    from apps.notifications.models import ParametreNotification
    from apps.notifications.forms import ParametreNotificationForm
    
    parametres, created = ParametreNotification.objects.get_or_create(utilisateur=user)
    form = ParametreNotificationForm(instance=parametres)
    
    if request.method == 'POST':
        form = ParametreNotificationForm(request.POST, instance=parametres)
        if form.is_valid():
            form.save()
            messages.success(request, "Vos paramètres de notification ont été mis à jour.")
            return redirect('accounts:notifications')
    
    # Marquer toutes les notifications comme lues (optionnel)
    # user.notifications.filter(lue=False).update(lue=True)
    
    context = {
        'notifications': notifications_list,
        'total_count': notifications_list.count(),
        'unread_count': notifications_list.filter(lue=False).count(),
        'form': form,
    }
    
    return render(request, 'promoteur/notifications.html', context)

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def marquer_notification_lue(request, notification_id):
    """
    API pour marquer une notification comme lue
    """
    try:
        notification = get_object_or_404(
            Notification, 
            id=notification_id, 
            utilisateur=request.user
        )
        notification.marquer_comme_lue()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def valider_documents(request):
    """
    Vue pour afficher les documents à valider (pour les administrateurs)
    """
    if not request.user.est_administrateur():
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    
    from apps.documents.models import Document
    
    documents_attente = Document.get_documents_en_attente()
    
    context = {
        'documents_attente': documents_attente,
    }
    
    return render(request, 'accounts/validate_documents.html', context)


# Dans views.py - Améliorez la fonction calculer_statistiques_utilisateurs
def calculer_statistiques_utilisateurs():
    """
    Calcule les statistiques pour les 4 cartes du dashboard
    """
    # Total des utilisateurs
    total = Utilisateur.objects.count()
    
    # Utilisateurs en attente de validation (basé sur les rôles)
    en_attente = Role.objects.filter(statut=StatutRole.EN_ATTENTE_VALIDATION).count()
    
    # Utilisateurs validés (rôles validés)
    valides = Role.objects.filter(statut=StatutRole.VALIDE).count()
    
    # Utilisateurs refusés (rôles refusés)
    refuses = Role.objects.filter(statut=StatutRole.REFUSE).count()
    
    return {
        'total': total,
        'en_attente': en_attente,
        'valides': valides,
        'refuses': refuses,
        # Pour la compatibilité avec l'ancien dashboard
        'total_utilisateurs': total,
        'utilisateurs_en_attente': en_attente,
    }

