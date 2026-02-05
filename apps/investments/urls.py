"""
URLs pour le module investments
Plateforme crowdBuilding - Burkina Faso
"""
from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [ 
    # NOUVELLE URL POUR LE DASHBOARD INVESTISSEUR
    path('dashboard/', views.dashboard_investisseur, name='dashboard_investisseur'),
    
    path('', views.list_investments, name='list'),
    path('mes-investissements/', views.mes_investissements, name='mes_investissements'),
    path('investir/<int:project_id>/', views.investir_projet, name='investir'),
    path('confirmation/<int:investment_id>/', views.confirmation_investissement, name='confirmation'),
    path('<int:investment_id>/', views.detail_investissement, name='detail'),
    
]