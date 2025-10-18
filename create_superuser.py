#!/usr/bin/env python
"""
Script pour créer un superutilisateur pour crowdBuilding
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crowdBuilding.settings')
django.setup()

from apps.accounts.models import Utilisateur, Role

def create_superuser():
    """Créer un superutilisateur"""
    email = 'admin@crowdbuilding.bf'
    password = 'admin123'
    nom = 'Administrateur'
    prenom = 'Super'
    
    # Vérifier si l'utilisateur existe déjà
    if Utilisateur.objects.filter(email=email).exists():
        print(f"L'utilisateur avec l'email {email} existe déjà.")
        return
    
    # Créer le superutilisateur
    user = Utilisateur.objects.create_superuser(
        email=email,
        password=password,
        nom=nom,
        prenom=prenom,
        telephone='+226 XX XX XX XX',
        profession='Administrateur système'
    )
    
    # Créer le rôle administrateur
    Role.objects.create(
        utilisateur=user,
        type='ADMINISTRATEUR',
        statut='VALIDE',
        role_actif=True
    )
    
    print(f"Superutilisateur créé avec succès !")
    print(f"Email: {email}")
    print(f"Mot de passe: {password}")
    print(f"Nom: {prenom} {nom}")

if __name__ == '__main__':
    create_superuser()
