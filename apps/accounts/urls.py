from django.urls import path
from django.contrib.auth import views as auth_views  # <-- AJOUTER CET IMPORT
from django.urls import reverse_lazy  # <-- AJOUTER CET IMPORT
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentification
    path('login/', views.ConnexionView.as_view(), name='login'),
    path('logout/', views.DeconnexionView.as_view(), name='logout'),
    path('register/', views.InscriptionView.as_view(), name='register'),
    
    # Profil utilisateur
    path('profile/', views.profil, name='profile'),
    path('profile/edit/', views.modifier_profil, name='edit_profile'),
    path('profile/change-password/', views.changer_mot_de_passe, name='change_password'),
    
    # Gestion des rôles
    path('switch-role/', views.basculer_role, name='switch_role'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.marquer_notification_lue, name='mark_notification_read'),
    
    # ===========================================
    # PASSWORD RESET URLs (AVEC IMPORTS CORRIGÉS)
    # ===========================================
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url=reverse_lazy('accounts:password_reset_done')
         ), 
         name='password_reset'),
    
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/',  # <-- URL CORRIGÉE (plus simple)
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete')
         ), 
         name='password_reset_confirm'),
    
    path('reset/complete/',  # <-- URL CORRIGÉE (plus simple)
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]