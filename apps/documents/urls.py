"""
URLs pour le module documents
Plateforme crowdBuilding - Burkina Faso
"""
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('upload/', views.upload_document, name='upload'),
    path('list/', views.list_documents, name='list'),
    path('<int:document_id>/', views.document_detail, name='detail'),
    path('<int:document_id>/delete/', views.delete_document, name='delete'),
    
]

