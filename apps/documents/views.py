"""
Vues pour le module documents
Plateforme crowdBuilding - Burkina Faso
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404

from .models import Document
from .forms import UploadDocumentForm

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from apps.accounts.models import Utilisateur

@login_required
def upload_document(request):
    """
    Uploader un document pour l'utilisateur connecté
    """
    if request.method == 'POST':
        form = UploadDocumentForm(request.POST, request.FILES, utilisateur=request.user)
        
        if form.is_valid():
            try:
                # Créer le document sans sauvegarder
                document = form.save(commit=False)
                
                # Définir le propriétaire
                document.proprietaire_id = request.user.id
                document.proprietaire_type = 'utilisateur'
                
                # Sauvegarder le document
                document.save()
                
                messages.success(
                    request, 
                    f'✅ Document "{document.nom}" uploadé avec succès ! '
                    f'Il sera examiné par nos administrateurs.'
                )
                return redirect('documents:upload')
                
            except Exception as e:
                messages.error(
                    request, 
                    f'❌ Erreur lors de l\'upload du document: {str(e)}'
                )
        else:
            messages.error(
                request, 
                '❌ Veuillez corriger les erreurs ci-dessous.'
            )
    else:
        form = UploadDocumentForm(utilisateur=request.user)
    
    # Récupérer les documents de l'utilisateur
    documents_utilisateur = Document.get_documents_utilisateur(request.user.id)
    
    context = {
        'form': form,
        'documents_utilisateur': documents_utilisateur,
    }
    
    return render(request, 'documents/upload.html', context)


@login_required
def list_documents(request):
    """
    Liste des documents de l'utilisateur connecté
    """
    documents = Document.get_documents_utilisateur(request.user.id)
    
    context = {
        'documents': documents,
    }
    
    return render(request, 'documents/list.html', context)


@login_required
def document_detail(request, document_id):
    """
    Détail d'un document spécifique
    """
    document = get_object_or_404(
        Document, 
        id=document_id,
        proprietaire_id=request.user.id,
        proprietaire_type='utilisateur'
    )
    
    context = {
        'document': document,
    }
    
    return render(request, 'documents/detail.html', context)


@login_required
def delete_document(request, document_id):
    """
    Supprimer un document (si pas encore validé)
    """
    document = get_object_or_404(
        Document,
        id=document_id,
        proprietaire_id=request.user.id,
        proprietaire_type='utilisateur'
    )
    
    # Ne permettre la suppression que si le document est en attente
    if document.statut != 'EN_ATTENTE':
        messages.error(
            request, 
            '❌ Impossible de supprimer ce document car il a déjà été traité.'
        )
        return redirect('documents:list')
    
    if request.method == 'POST':
        nom_document = document.nom
        document.delete()
        messages.success(request, f'✅ Document "{nom_document}" supprimé avec succès.')
        return redirect('documents:list')
    
    context = {
        'document': document,
    }
    
    return render(request, 'documents/confirm_delete.html', context)