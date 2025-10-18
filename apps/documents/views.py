"""
Vues pour le module documents
Plateforme crowdBuilding - Burkina Faso
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Document


@login_required
def upload_document(request):
    """Uploader un document"""
    if request.method == 'POST':
        # Logique d'upload du document
        messages.success(request, 'Document uploadé avec succès !')
        return redirect('documents:list')
    return render(request, 'documents/upload.html')


@login_required
def list_documents(request):
    """Liste des documents"""
    documents = Document.get_documents_utilisateur(request.user.id)
    return render(request, 'documents/list.html', {'documents': documents})


@login_required
def document_detail(request, document_id):
    """Détail d'un document"""
    document = Document.objects.get(id=document_id)
    return render(request, 'documents/detail.html', {'document': document})
