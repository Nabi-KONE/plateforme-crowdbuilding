"""
URLs pour le module projects
Plateforme crowdBuilding - Burkina Faso
"""
from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.list_projects, name='list'),
    path('<int:project_id>/', views.project_detail, name='detail'),
    path('create/', views.create_project, name='create'),
    path('my-projects/', views.my_projects, name='my_projects'),
    path('validate/<int:project_id>/', views.validate_project, name='validate'),
]
