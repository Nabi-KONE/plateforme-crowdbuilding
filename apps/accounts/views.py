"""
Vues pour la gestion des utilisateurs et des rôles
Plateforme crowdBuilding - Burkina Faso
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.documents import models

from .models import Utilisateur, Role
from .forms import InscriptionForm, ConnexionForm, ProfilForm, ChangementMotDePasseForm
from apps.notifications.models import Notification


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
    """
    Vue d'inscription
    """
    model = Utilisateur
    form_class = InscriptionForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        """Traitement du formulaire d'inscription"""
        try:
            with transaction.atomic():
                # Sauvegarder l'utilisateur et créer le rôle
                user = form.save()
                
                # Envoyer une notification de bienvenue
                Notification.objects.create(
                    utilisateur=user,
                    titre="Bienvenue sur crowdBuilding !",
                    contenu=f"Bonjour {user.prenom},\n\nVotre compte a été créé avec succès. Il est actuellement en attente de validation par nos administrateurs.\n\nVous recevrez une notification une fois votre compte validé.",
                    type='VALIDATION_COMPTE'
                )
                
                messages.success(
                    self.request, 
                    'Votre compte a été créé avec succès ! Vous pouvez maintenant vous connecter.'
                )
                return redirect(self.success_url)
                
        except Exception as e:
            messages.error(
                self.request, 
                'Une erreur est survenue lors de la création de votre compte. Veuillez réessayer.'
            )
            return self.form_invalid(form)


@login_required
def profil(request):
    """
    Vue de consultation et modification du profil
    """
    user = request.user
    role_actif = user.get_role_actif()
    
    # Statistiques de l'utilisateur
    stats = {}
    if user.est_promoteur():
        from apps.projects.models import Projet
        stats['total_projets'] = user.projets.count()
        stats['projets_valides'] = user.projets.filter(statut='VALIDE').count()
    elif user.est_investisseur():
        from apps.investments.models import Investissement
        stats['total_investissements'] = user.investissements.filter(statut='CONFIRME').count()
        stats['montant_investi'] = user.investissements.filter(statut='CONFIRME').aggregate(
            total=models.Sum('montant')
        )['total'] or 0
    
    context = {
        'user': user,
        'role_actif': role_actif,
        'stats': stats,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def modifier_profil(request):
    """
    Vue de modification du profil
    """
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
    Vue des notifications de l'utilisateur
    """
    user = request.user
    notifications_list = user.notifications.all()[:20]  # 20 dernières notifications
    
    # Marquer toutes les notifications comme lues
    user.notifications.filter(lue=False).update(lue=True)
    
    context = {
        'notifications': notifications_list,
    }
    
    return render(request, 'accounts/notifications.html', context)


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


@login_required
def valider_comptes(request):
    """
    Vue pour valider les comptes utilisateurs (pour les administrateurs)
    """
    if not request.user.est_administrateur():
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    
    from django.db.models import Q
    
    # Utilisateurs avec des rôles en attente
    utilisateurs_attente = Utilisateur.objects.filter(
        roles__statut='EN_ATTENTE_VALIDATION'
    ).distinct()
    
    context = {
        'utilisateurs_attente': utilisateurs_attente,
    }
    
    return render(request, 'accounts/validate_accounts.html', context)


@login_required
@require_http_methods(["POST"])
def valider_utilisateur(request, user_id):
    """
    Valider un utilisateur (pour les administrateurs)
    """
    if not request.user.est_administrateur():
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    
    try:
        user = get_object_or_404(Utilisateur, id=user_id)
        role_attente = user.roles.filter(statut='EN_ATTENTE_VALIDATION').first()
        
        if role_attente:
            role_attente.valider()
            
            # Créer une notification de validation
            Notification.creer_notification_validation_compte(user, valide=True)
            
            messages.success(request, f'Le compte de {user.nom_complet} a été validé avec succès.')
        else:
            messages.error(request, 'Aucun rôle en attente trouvé pour cet utilisateur.')
    
    except Exception as e:
        messages.error(request, f'Erreur lors de la validation: {str(e)}')
    
    return redirect('accounts:validate_accounts')


@login_required
@require_http_methods(["POST"])
def refuser_utilisateur(request, user_id):
    """
    Refuser un utilisateur (pour les administrateurs)
    """
    if not request.user.est_administrateur():
        messages.error(request, 'Accès non autorisé.')
        return redirect('core:dashboard')
    
    try:
        user = get_object_or_404(Utilisateur, id=user_id)
        motif = request.POST.get('motif', '')
        role_attente = user.roles.filter(statut='EN_ATTENTE_VALIDATION').first()
        
        if role_attente:
            role_attente.refuser()
            
            # Créer une notification de refus
            Notification.creer_notification_validation_compte(user, valide=False)
            
            messages.success(request, f'Le compte de {user.nom_complet} a été refusé.')
        else:
            messages.error(request, 'Aucun rôle en attente trouvé pour cet utilisateur.')
    
    except Exception as e:
        messages.error(request, f'Erreur lors du refus: {str(e)}')
    
    return redirect('accounts:validate_accounts')
