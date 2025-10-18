"""
URLs pour le module investments
Plateforme crowdBuilding - Burkina Faso
"""
from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('', views.list_investments, name='list'),
    path('my-investments/', views.my_investments, name='my_investments'),
    path('create/<int:project_id>/', views.create_investment, name='create'),
    path('<int:investment_id>/', views.investment_detail, name='detail'),
]
