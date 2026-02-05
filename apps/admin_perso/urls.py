# admin/urls.py - CHANGEZ LE NAMESPACE
from django.urls import path
from . import views

app_name = 'admin_perso'  

urlpatterns = [
    # ============================================
    # DASHBOARD ADMIN
    # ============================================
    path('', views.admin_dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # ============================================
    # GESTION DES UTILISATEURS
    # ============================================
    path('utilisateurs/', views.admin_gestion_utilisateurs, name='gestion_utilisateurs'),
    path('utilisateurs/<int:user_id>/', views.voir_details_utilisateur, name='details_utilisateur'),
    path('utilisateurs/<int:user_id>/valider/', views.valider_utilisateur_ajax, name='valider_utilisateur'),
    path('utilisateurs/<int:user_id>/refuser/', views.refuser_utilisateur_ajax, name='refuser_utilisateur'),
    path('utilisateurs/<int:user_id>/suspendre/', views.suspendre_utilisateur_ajax, name='suspendre_utilisateur'),
    
    # ============================================
    # GESTION DES PROJETS
    # ============================================
    path('projets/', views.admin_gestion_projets, name='gestion_projets'),
    path('projets/<int:project_id>/valider/', views.valider_projet_ajax, name='valider_projet'),
    path('projets/<int:project_id>/refuser/', views.refuser_projet_ajax, name='refuser_projet'),
    path('projets/<int:project_id>/partager/', views.partager_projet, name='partager_projet'),
    path('projets/<int:project_id>/suspendre/', views.suspendre_projet, name='suspendre_projet'),
    path('projets/<int:project_id>/demarrer-execution/', views.demarrer_execution, name='demarrer_execution'),
    path('projets/<int:project_id>/terminer/', views.terminer_projet, name='terminer_projet'),
    path('projets/<int:project_id>/valider-admin/', views.validate_project_admin, name='validate_project_admin'),
    path('projets/<int:project_id>/investisseurs/', views.admin_liste_investisseurs, name='liste_investisseurs'),
    path('promoteurs/<int:promoteur_id>/', views.admin_profil_promoteur, name='profil_promoteur'),
    
    # ============================================
    # GESTION DES INVESTISSEMENTS
    # ============================================
    path('investissements/', views.admin_gestion_investissements, name='gestion_investissements'),
    path('investissements/<int:investment_id>/valider/', views.valider_investissement, name='valider_investissement'),
    path('investissements/<int:investment_id>/rejeter/', views.rejeter_investissement, name='rejeter_investissement'),
    
    # ============================================
    # GESTION DES COMPTES RENDUS
    # ============================================
    path('comptes-rendus/', views.admin_liste_comptes_rendus, name='liste_comptes_rendus'),
    path('admin/comptes-rendus/<int:cr_id>/', views.admin_detail_compte_rendu, name='admin_detail_compte_rendu'),
    path('comptes-rendus/<int:cr_id>/valider/', views.admin_valider_compte_rendu, name='valider_compte_rendu'),
    path('comptes-rendus/<int:cr_id>/rejeter/', views.admin_rejeter_compte_rendu, name='rejeter_compte_rendu'),
    path('comptes-rendus/<int:cr_id>/demander-modification/', views.admin_demander_modification_compte_rendu, name='demander_modification_cr'),
    path('projets/<int:project_id>/comptes-rendus/', views.admin_comptes_rendus_projet, name='comptes_rendus_projet'),
    
    # ============================================
    # GESTION DES DOCUMENTS
    # ============================================
    path('documents/', views.validate_documents_list, name='validation_documents'),
    path('documents/<int:document_id>/action/', views.validate_document_action, name='validate_document_action'),
    path('documents/<int:document_id>/valider/', views.valider_document_ajax, name='valider_document'),
    path('documents/<int:document_id>/refuser/', views.refuser_document_ajax, name='refuser_document'),
]