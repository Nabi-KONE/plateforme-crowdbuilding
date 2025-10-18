"""
URLs pour le module accounts
Plateforme crowdBuilding - Burkina Faso
"""
from django.urls import path
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
    path('notifications/<int:notification_id>/mark-read/', views.marquer_notification_lue, name='mark_notification_read'),
    
    # Administration (pour les administrateurs)
    path('admin/validate-documents/', views.valider_documents, name='validate_documents'),
    path('admin/validate-accounts/', views.valider_comptes, name='validate_accounts'),
    path('admin/validate-user/<int:user_id>/', views.valider_utilisateur, name='validate_user'),
    path('admin/reject-user/<int:user_id>/', views.refuser_utilisateur, name='reject_user'),
]
