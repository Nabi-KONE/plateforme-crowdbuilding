"""
URLs pour le module core
Plateforme crowdBuilding - Burkina Faso
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Pages publiques
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('help/', views.help_center, name='help'),
    
    # Dashboard central (redirige vers le bon dashboard)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Dashboard admin (optionnel - si vous voulez un dashboard admin personnalisé)
    #path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]