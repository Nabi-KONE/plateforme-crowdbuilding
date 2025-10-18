"""
URLs pour le module notifications
Plateforme crowdBuilding - Burkina Faso
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.list_notifications, name='list'),
    path('<int:notification_id>/mark-read/', views.mark_read, name='mark_read'),
]
