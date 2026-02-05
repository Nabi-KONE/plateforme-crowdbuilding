# Créer un nouveau fichier : apps/documents/admin_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import Document

def is_administrateur(user):
    """Vérifie si l'utilisateur est administrateur"""
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_administrateur)
def admin_document_list(request):
    """Liste des documents pour validation (admin)"""
    # Documents en attente
    documents_attente = Document.get_documents_en_attente()

    # Debug: afficher les documents dans la console
    print(f"📋 Documents en attente: {documents_attente.count()}")
    for doc in documents_attente:
        print(f"  - {doc.nom} | Propriétaire: {doc.proprietaire_id} | Type: {doc.proprietaire_type}")
    
    # Documents récents
    documents_recents = Document.objects.all().order_by('-date_telechargement')[:50]
    
    context = {
        'documents_attente': documents_attente,
        'documents_recents': documents_recents,
        'section': 'documents',
    }
    
    return render(request, 'documents/admin_list.html', context)

@login_required
@user_passes_test(is_administrateur)
def admin_document_detail(request, document_id):
    """Détail d'un document pour validation admin"""
    document = get_object_or_404(Document, id=document_id)
    
    context = {
        'document': document,
        'section': 'documents',
    }
    
    return render(request, 'documents/admin_detail.html', context)

@login_required
@user_passes_test(is_administrateur)
def valider_document(request, document_id):
    """Valider un document"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        try:
            document.valider(request.user)
            messages.success(request, f'✅ Document "{document.nom}" validé avec succès!')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Document validé'})
                
        except Exception as e:
            messages.error(request, f'❌ Erreur: {str(e)}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})
    
    return redirect('documents:admin_list')

@login_required
@user_passes_test(is_administrateur)
def refuser_document(request, document_id):
    """Refuser un document avec motif"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        motif = request.POST.get('motif_refus', '').strip()
        
        if not motif:
            messages.error(request, '❌ Veuillez saisir un motif de refus.')
        else:
            try:
                document.refuser(request.user, motif)
                messages.success(request, f'✅ Document "{document.nom}" refusé.')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'message': 'Document refusé'})
                    
            except Exception as e:
                messages.error(request, f'❌ Erreur: {str(e)}')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': str(e)})
    
    return redirect('documents:admin_list')


# Ajoutez dans admin_views.py
@login_required
@user_passes_test(is_administrateur)
def debug_admin(request):
    """Vue de debug temporaire"""
    documents_attente = Document.get_documents_en_attente()
    context = {'documents_attente': documents_attente}
    return render(request, 'documents/debug_admin.html', context)