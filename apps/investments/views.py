"""
Vues pour le module investments
Plateforme crowdBuilding - Burkina Faso
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Investissement


def list_investments(request):
    """Liste des investissements (pour les administrateurs)"""
    investments = Investissement.objects.all()
    return render(request, 'investments/list.html', {'investments': investments})


@login_required
def my_investments(request):
    """Mes investissements"""
    investments = request.user.investissements.all()
    return render(request, 'investments/my_investments.html', {'investments': investments})


@login_required
def create_investment(request, project_id):
    """Créer un investissement"""
    if request.method == 'POST':
        # Logique de création de l'investissement
        messages.success(request, 'Investissement créé avec succès !')
        return redirect('investments:my_investments')
    return render(request, 'investments/create.html', {'project_id': project_id})


@login_required
def investment_detail(request, investment_id):
    """Détail d'un investissement"""
    investment = get_object_or_404(Investissement, id=investment_id)
    return render(request, 'investments/detail.html', {'investment': investment})
