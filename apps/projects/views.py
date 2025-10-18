"""
Vues pour le module projects
Plateforme crowdBuilding - Burkina Faso
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Projet


def list_projects(request):
    """Liste tous les projets publics"""
    projects = Projet.objects.filter(statut__in=['VALIDE', 'EN_COURS_FINANCEMENT'])
    return render(request, 'projects/list.html', {'projects': projects})


def project_detail(request, project_id):
    """Détail d'un projet"""
    project = get_object_or_404(Projet, id=project_id)
    return render(request, 'projects/detail.html', {'project': project})


@login_required
def create_project(request):
    """Créer un nouveau projet"""
    if request.method == 'POST':
        # Logique de création du projet
        messages.success(request, 'Projet créé avec succès !')
        return redirect('projects:list')
    return render(request, 'projects/create.html')


@login_required
def my_projects(request):
    """Mes projets (pour les promoteurs)"""
    projects = request.user.projets.all()
    return render(request, 'projects/my_projects.html', {'projects': projects})


@login_required
def validate_project(request, project_id):
    """Valider un projet (pour les administrateurs)"""
    project = get_object_or_404(Projet, id=project_id)
    if request.method == 'POST':
        project.valider(request.user)
        messages.success(request, 'Projet validé avec succès !')
    return redirect('projects:detail', project_id=project.id)
