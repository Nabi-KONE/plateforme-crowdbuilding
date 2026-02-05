from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # ============================================
    # URLs PUBLIQUES
    # ============================================
    path('', views.list_projects, name='list'),
    path('<int:project_id>/', views.project_detail, name='detail'),
    
    # ============================================
    # URLs ESPACE PROMOTEUR
    # ============================================
    path('promoteur/dashboard/', views.dashboard_promoteur, name='promoteur_dashboard'),
    path('promoteur/projets/', views.mes_projets_promoteur, name='promoteur_projets'),
    path('promoteur/nouveau-projet/', views.nouveau_projet_promoteur, name='promoteur_nouveau_projet'),
    path('promoteur/projet/<int:project_id>/', views.detail_projet_promoteur, name='promoteur_projet_detail'),
    path('promoteur/compte-rendu/', views.gestion_compte_rendu, name='promoteur_compte_rendu'),
    path('promoteur/nouveau-projet/etapes/<int:projet_id>/', views.nouveau_projet_etapes, name='promoteur_nouveau_projet_etapes'),
    path('promoteur/etapes/', views.gestion_etapes, name='promoteur_etapes'),
    path('promoteur/etapes/<int:projet_id>/', views.gestion_etapes, name='promoteur_etapes_projet'),
    path('promoteur/confirmation-projet/<int:projet_id>/', views.confirmation_projet, name='promoteur_confirmation_projet'),

    # URL pour CRÉER un compte rendu SANS projet spécifique
    path('promoteur/compte-rendu/nouveau/', views.nouveau_compte_rendu, name='nouveau_compte_rendu'),
    
    # URL pour CRÉER un compte rendu AVEC projet spécifique (OPTIMALE)
    path('promoteur/compte-rendu/creer/<int:projet_id>/', views.nouveau_compte_rendu, name='creer_compte_rendu_projet'),# Ajoutez cette URL
    # Une seule URL pour les étapes AJAX
    path('ajax/get-etapes-projet/', views.ajax_get_etapes_projet, name='ajax_get_etapes_projet'),
    path('notifications/', views.notifications_promoteur, name='notifications')


    
]