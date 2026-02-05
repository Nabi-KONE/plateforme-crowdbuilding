"""
Modèles pour la gestion des projets immobiliers
Plateforme crowdBuilding - Burkina Faso
"""
from .utils import get_administrateurs, envoyer_notification_aux_administrateurs
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import Utilisateur
import os
import uuid

def projet_image_path(instance, filename):
    """Génère le chemin pour les images des projets"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f'projets/{instance.projet.id}/images/{filename}'

def projet_document_path(instance, filename):
    """Génère le chemin pour les documents des projets"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f'projets/{instance.projet.id}/documents/{filename}'

def projet_image_garde_path(instance, filename):
    """Génère le chemin pour l'image de garde"""
    ext = filename.split('.')[-1]
    filename = f"garde-{uuid.uuid4()}.{ext}"
    return f'projets/{instance.id}/garde/{filename}'

def document_obligatoire_path(instance, filename):
    """Génère le chemin pour les documents obligatoires"""
    ext = filename.split('.')[-1]
    filename = f"{instance.type_document}-{uuid.uuid4()}.{ext}"
    return f'projets/{instance.projet.id}/documents-obligatoires/{filename}'

class StatutProjet(models.TextChoices):
    BROUILLON = 'BROUILLON', 'Brouillon'
    A_COMPLETER = 'A_COMPLETER', 'À compléter'
    EN_ATTENTE_VALIDATION = 'EN_ATTENTE_VALIDATION', 'En attente de validation'
    VALIDE = 'VALIDE', 'Validé'
    REFUSE = 'REFUSE', 'Refusé'
    EN_CAMPAGNE = 'EN_CAMPAGNE', 'En campagne'
    FINANCE = 'FINANCE', 'Financé'
    EN_COURS_EXECUTION = 'EN_COURS_EXECUTION', 'En cours d’exécution'
    TERMINE = 'TERMINE', 'Terminé'
    SUSPENDU = 'SUSPENDU', 'Suspendu'   # ✅ AJOUTER ABSOLUMENT


class Projet(models.Model):
    """
    Modèle pour les projets immobiliers
    Un promoteur peut soumettre un projet pour le financement participatif
    """
    
    # CATÉGORIE IMMOBILIER
    TYPE_IMMOBILIER_CHOICES = [
        ('RESIDENTIEL', 'Résidentiel'),
        ('COMMERCIAL', 'Commercial'),
        ('BUREAUX', 'Bureaux'),
        ('INDUSTRIEL', 'Industriel'),
    ]
        
    # Informations de base
    reference = models.CharField(max_length=20, unique=True, verbose_name="Référence")
    titre = models.CharField(max_length=200, verbose_name="Titre du projet")
    description = models.TextField(verbose_name="Description détaillée")
    resume = models.TextField(default="Aucun résumé")
    
    # Catégorie du projet immobilier
    categorie = models.CharField(
        max_length=50,
        choices=TYPE_IMMOBILIER_CHOICES,
        default='RESIDENTIEL',
        verbose_name="Type de projet immobilier"
    )
    
    # Image de garde
    image_garde = models.ImageField(
        upload_to=projet_image_garde_path,
        null=True,
        blank=True,
        verbose_name="Image de garde"
    )

    # Informations financières
    montant_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(100000)],  # Minimum 100 000 FCFA
        verbose_name="Montant total (FCFA)"
    )

    prix_unitaire = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,           # Permettre NULL
        blank=True,          # Permettre vide dans les formulaires
        default=0,           # Valeur par défaut
        verbose_name="Prix unitaire d'une part (FCFA)",
        help_text="Prix fixé manuellement par le promoteur pour chaque part"
    )

    nombre_total_parts = models.IntegerField(
        default=1000,
        validators=[MinValueValidator(10), MaxValueValidator(100000)],
        verbose_name="Nombre total de parts"
    )

    montant_collecte = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=0,
        verbose_name="Montant collecté (FCFA)"
    )
    montant_min_investissement = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1000,
        validators=[MinValueValidator(100)],
        verbose_name="Montant minimum d'investissement (FCFA)"
    )
    nombre_min_parts = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Nombre minimum de parts à acheter",
    )
    
    # 1.3 - Mettre à jour le champ duree (déjà en mois mais sans help text)
    duree = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        verbose_name="Durée de réalisation (mois)",
        help_text="Durée prévisionnelle de réalisation en mois"
    )

    date_debut = models.DateField(verbose_name="Date de début prévue")
    date_fin = models.DateField(verbose_name="Date de fin prévue")
    
    # Localisation
    localisation = models.CharField(max_length=200, verbose_name="Localisation")
    ville = models.CharField(max_length=100, default="Ouagadougou", verbose_name="Ville")
    region = models.CharField(max_length=100, default="Centre", verbose_name="Région")
    adresse_complete = models.TextField(verbose_name="Adresse complète", blank=True)
    
    # Métadonnées
    promoteur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='projets',
        verbose_name="Promoteur"
    )
    statut = models.CharField(
        max_length=25,
        choices=StatutProjet.choices,
        default=StatutProjet.EN_ATTENTE_VALIDATION,
        verbose_name="Statut du projet"
    )
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    date_publication = models.DateTimeField(null=True, blank=True, verbose_name="Date de publication")
    
    # Gestion des étapes
    etapes_definies = models.BooleanField(default=False, verbose_name="Étapes définies")
    date_debut_execution = models.DateField(null=True, blank=True, verbose_name="Date de début d'exécution")
    
    # Informations supplémentaires
    motif_refus = models.TextField(blank=True, verbose_name="Motif de refus")
    administrateur_validateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projets_valides',
        verbose_name="Administrateur validateur"
    )
    
    duree_campagne = models.IntegerField(
        default=3,  # 3 mois par défaut au lieu de 60 jours
        validators=[MinValueValidator(1), MaxValueValidator(24)],  # 1 à 24 mois
        verbose_name="Durée de collecte (mois)",
        help_text="Durée de la campagne de collecte en mois (1 à 24 mois)"
    )

    # 1.2 - Ajouter un champ pour le seuil de déclenchement (100% fixe selon description)
    seuil_declenchement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,  # Toujours 100% selon description
        verbose_name="Seuil de déclenchement",
        help_text="Seuil de déclenchement fixé à 100%"
    )
    # AJOUTER DANS Projet(models.Model)

    statut_precedent = models.CharField(
        max_length=25,
        choices=StatutProjet.choices,
        null=True,
        blank=True,
        verbose_name="Statut précédent avant suspension"
    )

    motif_suspension = models.TextField(
        blank=True,
        verbose_name="Motif de suspension"
    )
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.reference} - {self.titre}"
    
    def save(self, *args, **kwargs):
        """Override save pour générer automatiquement la référence"""
        if not self.reference:
            # Générer une référence unique : PROJ-YYYY-XXXX
            year = timezone.now().year
            last_project = Projet.objects.filter(
                date_creation__year=year
            ).order_by('-date_creation').first()
            
            if last_project and last_project.reference:
                try:
                    last_number = int(last_project.reference.split('-')[-1])
                    new_number = last_number + 1
                except (ValueError, IndexError):
                    new_number = 1
            else:
                new_number = 1
            
            self.reference = f'PROJ-{year}-{new_number:04d}'
        
        # Mettre à jour le résumé si la description change
        if self.description and (not self.resume or self.resume == "Aucun résumé"):
            self.resume = self.description[:200] + ("..." if len(self.description) > 200 else "")
        
        super().save(*args, **kwargs)
    
    @property
    def image_principale(self):
        """Retourne l'image principale du projet"""
        if self.image_garde:
            return self.image_garde
        image = self.images.filter(est_principale=True).first()
        if not image:
            image = self.images.first()
        return image.image if image else None
    
    @property
    def taux_financement(self):
        """Calcule le pourcentage de financement atteint"""
        if self.montant_total > 0:
            return (self.montant_collecte / self.montant_total) * 100
        return 0
    
    @property
    def montant_restant(self):
        """Calcule le montant restant à financer"""
        return max(0, self.montant_total - self.montant_collecte)
    
    @property
    def est_finance_complet(self):
        """Vérifie si le projet est entièrement financé"""
        return self.montant_collecte >= self.montant_total
    

    def finaliser_financement(self):
        if self.est_finance_complet:
            self.statut = StatutProjet.FINANCE
            self.save()

    
    @property
    def est_financeable(self):
        """Vérifie si le projet peut recevoir des investissements"""
        return self.statut in [
            StatutProjet.VALIDE,
            StatutProjet.EN_CAMPAGNE,
            StatutProjet.FINANCE
        ]
    
    @property
    def jours_restants(self):
        """Calcule le nombre de jours restants pour le financement"""
        if self.date_fin:
            today = timezone.now().date()
            jours_restants = (self.date_fin - today).days
            return max(0, jours_restants)
        return 0

    @property
    def peut_ajouter_compte_rendu(self):
        """Vérifie si le promoteur peut ajouter un compte rendu"""
        return self.statut in [
            StatutProjet.EN_CAMPAGNE,
            StatutProjet.EN_COURS_EXECUTION
        ]
    
    @property
    def peut_definir_etapes(self):
        """Vérifie si le promoteur peut définir des étapes pour ce projet"""
        return self.statut in [
            StatutProjet.VALIDE, 
            StatutProjet.EN_CAMPAGNE, 
            StatutProjet.EN_COURS_EXECUTION,
            StatutProjet.FINANCE
        ]
    
    @property
    def peut_soumettre_validation(self):
        """Vérifie si le projet peut être soumis pour validation"""
        return self.statut == StatutProjet.BROUILLON and self.documents_obligatoires.filter(est_obligatoire=True).count() >= 2
    
    @property
    def documents_obligatoires_complets(self):
        """Vérifie si tous les documents obligatoires sont fournis"""
        documents_obligatoires = self.documents_obligatoires.filter(est_obligatoire=True)
        return documents_obligatoires.count() >= 2  # Au moins 2 documents obligatoires
    
    # ✅ AJOUTER cette nouvelle propriété
    @property
    def documents(self):
        """Retourne tous les documents associés à ce projet via l'app documents"""
        try:
            from apps.documents.models import Document
            return Document.objects.filter(proprietaire_type='projet', proprietaire_id=self.id)
        except ImportError:
            # Retourner un queryset vide si l'app documents n'est pas disponible
            from django.db.models import QuerySet
            return QuerySet().none()
        
    def get_statut_color(self):
        """Retourne la couleur Bootstrap selon le statut"""
        colors = {
            'BROUILLON': 'secondary',
            'EN_ATTENTE_VALIDATION': 'warning',
            'A_COMPLETER': 'warning',
            'VALIDE': 'success',
            'REFUSE': 'danger',
            'EN_CAMPAGNE': 'info',
            'FINANCE': 'primary',
            'EN_COURS_EXECUTION': 'info',
            'TERMINE': 'success',
            'ANNULE': 'danger'
        }
        return colors.get(self.statut, 'secondary')
    
    def soumettre_validation(self):
        """Soumet le projet pour validation"""
        if self.statut == StatutProjet.BROUILLON and self.documents_obligatoires_complets:
            self.statut = StatutProjet.EN_ATTENTE_VALIDATION
            self.save()
            return True
        return False
    
    def valider(self, administrateur):
        """Valide le projet par un administrateur"""
        self.statut = StatutProjet.VALIDE
        self.date_validation = timezone.now()
        self.administrateur_validateur = administrateur
        self.motif_refus = ""
        self.save()
    
    def refuser(self, administrateur, motif):
        """Refuse le projet avec un motif"""
        self.statut = StatutProjet.REFUSE
        self.administrateur_validateur = administrateur
        self.motif_refus = motif
        self.save()
    
    def lancer_campagne(self):
        """Lance la campagne de financement"""
        if self.statut == StatutProjet.VALIDE:
            self.statut = StatutProjet.EN_CAMPAGNE
            self.save()
    
    def demarrer_execution(self):
        """Démarre l'exécution du projet"""
        if self.statut == StatutProjet.FINANCE:
            self.statut = StatutProjet.EN_COURS_EXECUTION
            self.date_debut_execution = timezone.now().date()
            self.save()
    
    def definir_etapes(self):
        """Marque le projet comme ayant des étapes définies"""
        self.etapes_definies = True
        self.save()

    def get_absolute_url(self):
        """
        Retourne l'URL absolue pour voir les détails du projet
        """
        from django.urls import reverse
        return reverse('projects:detail', kwargs={'project_id': self.id})
    

    # AJOUTER cette propriété
    @property
    def valeur_part(self):
        """Retourne la valeur d'une part (rétrocompatible)"""
        # Priorité 1 : prix_unitaire défini manuellement
        if self.prix_unitaire and self.prix_unitaire > 0:
            return self.prix_unitaire
        
        # Priorité 2 : calcul automatique
        if self.nombre_total_parts and self.nombre_total_parts > 0 and self.montant_total:
            return self.montant_total / self.nombre_total_parts
        
        return 0
    
    # AJOUTER cette propriété pour calculer la date de fin
    @property
    def date_fin_calculee(self):
        """Calcule la date de fin basée sur la date de début et la durée"""
        if self.date_debut and self.duree:
            return self.date_debut + timedelta(days=self.duree)
        return None
    
    @property
    def investisseurs_count(self):
        """Retourne le nombre d'investisseurs uniques"""
        from apps.investments.models import Investissement  # Ajustez selon votre app
        return self.investissements.values('investisseur').distinct().count()
    
    @property
    def total_investi(self):
        """Retourne le montant total investi"""
        return self.montant_collecte  # Ou une logique plus complexe si besoin
    
    parts_vendues = models.PositiveIntegerField(
        default=0,
        verbose_name="Parts vendues"
    )
        
    @property
    def parts_restantes(self):
        return self.nombre_total_parts - self.parts_vendues
    
    
    # Champs pour la validation des documents (si vous voulez tracker l'état)
    document_foncier_valide = models.BooleanField(default=False, verbose_name="Document foncier validé")
    document_foncier_rejete = models.BooleanField(default=False, verbose_name="Document foncier rejeté")
    document_foncier_motif_rejet = models.TextField(blank=True, verbose_name="Motif de rejet document foncier")
    
    document_technique_valide = models.BooleanField(default=False, verbose_name="Document technique validé")
    document_technique_rejete = models.BooleanField(default=False, verbose_name="Document technique rejeté")
    document_technique_motif_rejet = models.TextField(blank=True, verbose_name="Motif de rejet document technique")
    
    document_financier_valide = models.BooleanField(default=False, verbose_name="Document financier validé")
    document_financier_rejete = models.BooleanField(default=False, verbose_name="Document financier rejeté")
    document_financier_motif_rejet = models.TextField(blank=True, verbose_name="Motif de rejet document financier")

class DocumentObligatoire(models.Model):
    """
    Documents obligatoires pour la soumission d'un projet
    """
    TYPE_DOCUMENT_CHOICES = [
        ('ETUDE_FACTIBILITE', 'Étude de faisabilité'),
        ('PLAN_ARCHITECTURAL', 'Plan architectural'),
        ('PERMIS_CONSTRUIRE', 'Permis de construire'),
        ('BUSINESS_PLAN', 'Business plan'),
        ('TECHNIQUE', 'Document technique'),
        ('AUTRE', 'Autre'),
    ]
    
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='documents_obligatoires',
        verbose_name="Projet"
    )
    type_document = models.CharField(
        max_length=50,
        choices=TYPE_DOCUMENT_CHOICES,
        verbose_name="Type de document"
    )
    nom = models.CharField(max_length=200, verbose_name="Nom du document")
    fichier = models.FileField(
        upload_to=document_obligatoire_path,
        verbose_name="Fichier"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    est_obligatoire = models.BooleanField(default=True, verbose_name="Document obligatoire")
    date_depot = models.DateTimeField(default=timezone.now, verbose_name="Date de dépôt")

    class Meta:
        verbose_name = "Document obligatoire"
        verbose_name_plural = "Documents obligatoires"
        ordering = ['type_document']
    
    def __str__(self):
        return f"{self.get_type_document_display()} - {self.projet.titre}"
    
    def save(self, *args, **kwargs):
        """Auto-complète le nom si vide"""
        if not self.nom:
            self.nom = f"{self.get_type_document_display()} - {self.projet.titre}"
        super().save(*args, **kwargs)

    def valider(self, administrateur):
        """Valider le document"""
        self.est_valide = True
        self.est_rejete = False
        self.motif_rejet = ""
        self.date_validation = timezone.now()
        self.administrateur_validateur = administrateur
        self.save()
    
    def refuser(self, administrateur, motif):
        """Refuser le document"""
        self.est_valide = False
        self.est_rejete = True
        self.motif_rejet = motif
        self.date_validation = timezone.now()
        self.administrateur_validateur = administrateur
        self.save()

class ImageProjet(models.Model):
    """Images associées à un projet"""
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Projet"
    )
    image = models.ImageField(
        upload_to=projet_image_path,
        verbose_name="Image"
    )
    legende = models.CharField(max_length=200, blank=True, verbose_name="Légende")
    est_principale = models.BooleanField(default=False, verbose_name="Image principale")
    date_ajout = models.DateTimeField(default=timezone.now, verbose_name="Date d'ajout")
    
    class Meta:
        verbose_name = "Image de projet"
        verbose_name_plural = "Images de projet"
        ordering = ['-est_principale', 'date_ajout']
    
    def __str__(self):
        return f"Image pour {self.projet.titre}"
    
    def save(self, *args, **kwargs):
        """S'assure qu'une seule image est principale"""
        if self.est_principale:
            # Désactiver les autres images principales
            ImageProjet.objects.filter(
                projet=self.projet, 
                est_principale=True
            ).update(est_principale=False)
        super().save(*args, **kwargs)

class DocumentProjet(models.Model):
    """Documents associés à un projet"""
    TYPE_DOCUMENT_CHOICES = [
        ('ETUDE_FACTIBILITE', 'Étude de faisabilité'),
        ('PLAN_ARCHITECTURAL', 'Plan architectural'),
        ('PERMIS_CONSTRUIRE', 'Permis de construire'),
        ('CONTRAT', 'Contrat'),
        ('RAPPORT', 'Rapport'),
        ('AUTRE', 'Autre'),
    ]
    
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Projet"
    )
    type_document = models.CharField(
        max_length=50,
        choices=TYPE_DOCUMENT_CHOICES,
        verbose_name="Type de document"
    )
    nom = models.CharField(max_length=200, verbose_name="Nom du document")
    fichier = models.FileField(
        upload_to=projet_document_path,
        verbose_name="Fichier"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    date_ajout = models.DateTimeField(default=timezone.now, verbose_name="Date d'ajout")
    est_public = models.BooleanField(default=True, verbose_name="Document public")
    
    class Meta:
        verbose_name = "Document de projet"
        verbose_name_plural = "Documents de projet"
        ordering = ['-date_ajout']
    
    def __str__(self):
        return f"{self.nom} - {self.projet.titre}"

# Dans la classe Etape, remplacer/modifier :
class Etape(models.Model):
    """
    Modèle pour les étapes de réalisation d'un projet
    """
    # Dans la classe Etape - ajouter ce champ
    STATUT_ETAPE_CHOICES = [
        ('A_VENIR', 'À venir'),
        ('EN_COURS', 'En cours'),
        ('TERMINEE', 'Terminée'),
        ('RETARD', 'En retard'),
    ]

    statut = models.CharField(
        max_length=20,
        choices=STATUT_ETAPE_CHOICES,
        default='A_VENIR',
        verbose_name="Statut de l'étape"
    )

    # Méthodes utilitaires (ajouter à la classe Etape)
    def mettre_en_cours(self):
        """Marque l'étape comme en cours"""
        self.statut = 'EN_COURS'
        self.save()

    def terminer(self):
        """Termine l'étape"""
        self.statut = 'TERMINEE'
        self.terminee = True
        self.date_realisation = timezone.now()
        self.save()

    def marquer_en_retard(self):
        """Marque l'étape comme en retard"""
        self.statut = 'RETARD'
        self.save()

    @property
    def est_en_retard(self):
        """Détermine automatiquement si l'étape est en retard"""
        if not self.terminee and self.date_fin:
            return timezone.now().date() > self.date_fin
        return False

    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='etapes',
        verbose_name="Projet"
    )
    titre = models.CharField(max_length=200, verbose_name="Titre de l'étape")
    description = models.TextField(verbose_name="Description")
    ordre = models.IntegerField(verbose_name="Ordre")
    duree_estimee = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Durée estimée (mois)",
        validators=[MinValueValidator(1)]
    )
    date_debut = models.DateField(null=True, blank=True, verbose_name="Date de début prévue")
    date_publication = models.DateTimeField(default=timezone.now, verbose_name="Date de publication")
    date_realisation = models.DateTimeField(null=True, blank=True, verbose_name="Date de réalisation")
    terminee = models.BooleanField(default=False, verbose_name="Terminée")
    
    class Meta:
        verbose_name = "Étape"
        verbose_name_plural = "Étapes"
        ordering = ['ordre']
        unique_together = ['projet', 'ordre']
    
    def __str__(self):
        return f"{self.projet.titre} - Étape {self.ordre}: {self.titre}"
    
    @property
    def date_fin(self):
        """Calcule la date de fin à partir de la date de début et de la durée"""
        if self.date_debut and self.duree_estimee:
            from datetime import timedelta
            # Approx 30 jours par mois
            jours = self.duree_estimee * 30
            return self.date_debut + timedelta(days=jours)
        return None
    
    @property
    def duree_estimee_jours(self):
        """Retourne la durée en jours"""
        if self.duree_estimee:
            return self.duree_estimee * 30
        return None
    
    def valider(self):
        """Valide l'étape"""
        self.terminee = True
        self.date_realisation = timezone.now()
        self.save()
    
    @property
    def peut_modifier(self):
        """Vérifie si l'étape peut être modifiée"""
        return not self.terminee
    
    @property
    def est_en_retard(self):
        """Vérifie si l'étape est en retard"""
        if self.date_fin and not self.terminee:
            return timezone.now().date() > self.date_fin
        return False
    
    @property
    def statut_couleur(self):
        """Retourne la couleur du statut"""
        if self.terminee:
            return 'success'
        elif self.est_en_retard:
            return 'danger'
        else:
            return 'warning'

# Dans apps/projects/models.py

import os
from uuid import uuid4
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.urls import reverse
from apps.accounts.models import Utilisateur

# ============================================
# FONCTIONS UTILITAIRES
# ============================================

def image_compte_rendu_path(instance, filename):
    """Génère le chemin pour les images des comptes rendus"""
    ext = filename.split('.')[-1]
    filename = f"cr_{uuid4().hex[:8]}.{ext}"
    return f'comptes_rendus/{instance.compte_rendu.projet.id}/{instance.compte_rendu.id}/{filename}'

def validate_image_size(value):
    """Valide la taille de l'image (max 10MB)"""
    limit = 10 * 1024 * 1024  # 10MB
    if value.size > limit:
        raise ValidationError('La taille du fichier ne doit pas dépasser 10MB.')

# ============================================
# MODÈLE COMPTE_RENDU
# ============================================

class CompteRendu(models.Model):
    """
    Modèle pour les comptes rendus de projet
    """
    STATUT_CHOICES = [
        ('EN_ATTENTE_VALIDATION', 'En attente de validation'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
        ('A_MODIFIER', 'À modifier'),  # ← AJOUTER CE STATUT
    ]
    
    projet = models.ForeignKey(
        'Projet',
        on_delete=models.CASCADE,
        related_name='comptes_rendus',
        verbose_name="Projet"
    )
    
    etape = models.ForeignKey(
        'Etape',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comptes_rendus',
        verbose_name="Étape concernée",
        help_text="Optionnel : lier ce compte rendu à une étape spécifique"
    )
    
    titre = models.CharField(max_length=200, verbose_name="Titre")
    contenu = models.TextField(verbose_name="Contenu")
    
    date_creation = models.DateTimeField(default=timezone.now, verbose_name="Date de création")
    date_publication = models.DateTimeField(null=True, blank=True, verbose_name="Date de publication")
    
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='EN_ATTENTE_VALIDATION',
        verbose_name="Statut de validation"
    )
    
    avancement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        verbose_name="Avancement (%)"
    )
    
    motif_rejet = models.TextField(blank=True, verbose_name="Motif de rejet")
    
    administrateur_validateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comptes_rendus_valides',
        verbose_name="Administrateur validateur"
    )
    
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    
    class Meta:
        verbose_name = "Compte rendu"
        verbose_name_plural = "Comptes rendus"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['projet', 'statut']),
            models.Index(fields=['date_creation']),
            models.Index(fields=['statut']),
        ]
    
    def __str__(self):
        return f"{self.projet.titre} - {self.titre}"
    
    # ========== MÉTHODES MÉTIER ==========

    def get_absolute_url(self):
        """URL absolue du compte rendu"""
        from django.urls import reverse
        return reverse('admin_perso:admin_detail_compte_rendu',kwargs={'cr_id': self.id})

    
    def soumettre(self):
        """Soumet le compte rendu pour validation"""
        self.statut = 'EN_ATTENTE_VALIDATION'
        self.save()
        self.envoyer_notification_soumission()
    
    def valider(self, administrateur):
        """Valide le compte rendu"""
        self.statut = 'VALIDE'
        self.administrateur_validateur = administrateur
        self.date_validation = timezone.now()
        self.date_publication = timezone.now()
        self.motif_rejet = ""
        self.save()
        self.envoyer_notification_validation()
    
    def refuser(self, administrateur, motif):
        """Refuse le compte rendu avec un motif"""
        self.statut = 'REJETE'
        self.administrateur_validateur = administrateur
        self.date_validation = timezone.now()
        self.motif_rejet = motif
        self.save()
        self.envoyer_notification_rejet()
    
    # ========== NOTIFICATIONS ==========
    
    def envoyer_notification_soumission(self):
        """Envoie une notification aux administrateurs"""
        # Utiliser la fonction utilitaire
        succes = envoyer_notification_aux_administrateurs(
            titre="📄 Nouveau compte rendu soumis",
            contenu=f"Le promoteur {self.projet.promoteur.get_full_name()} a soumis un compte rendu pour le projet '{self.projet.titre}'.",
            type_notif='NOUVEAU_COMPTE_RENDU',
            lien=self.get_absolute_url()
        )
        
        if not succes:
            # Fallback: log
            print(f"📢 Compte rendu soumis (notifications échouées): {self.titre}")
    
    def envoyer_notification_validation(self):
        """Notification au promoteur pour validation"""
        try:
            from apps.notifications.models import Notification
            
            Notification.objects.create(
                utilisateur=self.projet.promoteur,
                titre="✅ Compte rendu validé",
                contenu=f"Votre compte rendu '{self.titre}' pour le projet '{self.projet.titre}' a été validé par l'administration.",
                type='VALIDATION_COMPTE_RENDU',
                lien=self.get_absolute_url()
            )
        except Exception as e:
            print(f"Erreur notification validation: {e}")

    
    def envoyer_notification_rejet(self):
        """Notification au promoteur pour rejet"""
        try:
            from apps.notifications.models import Notification
            
            Notification.objects.create(
                utilisateur=self.projet.promoteur,
                titre="❌ Compte rendu rejeté",
                contenu=f"Votre compte rendu '{self.titre}' a été rejeté. Motif : {self.motif_rejet}",
                type='REJET_COMPTE_RENDU',
                important=True,
                lien=self.get_absolute_url()
            )
        except Exception as e:
            print(f"Erreur notification rejet: {e}")
    
    # ========== PROPRIÉTÉS ==========
    
    @property
    def est_public(self):
        """Vérifie si le compte rendu est visible publiquement"""
        return self.statut == 'VALIDE'
    
    @property
    def peut_modifier(self):
        """Vérifie si le compte rendu peut être modifié"""
        return self.statut in ['EN_ATTENTE_VALIDATION', 'REJETE']
    
    @property
    def images_count(self):
        """Nombre d'images associées"""
        return self.images.count()
    
    @property
    def images_valides(self):
        """Images validées seulement"""
        return self.images.filter(est_valide=True)
    
    @property
    def est_recent(self):
        """Vérifie si le compte rendu est récent (< 7 jours)"""
        return (timezone.now() - self.date_creation).days < 7
    
    @property
    def duree_attente(self):
        """Durée d'attente depuis la soumission"""
        if self.statut == 'EN_ATTENTE_VALIDATION':
            return timezone.now() - self.date_creation
        return None
    
    def demander_modifications(self, administrateur, commentaires):
        """Demande des modifications sur le compte rendu"""
        self.statut = 'A_MODIFIER'
        self.administrateur_validateur = administrateur
        self.date_validation = timezone.now()
        self.save()
        
        # Créer une demande de modification
        from .models import DemandeModificationCompteRendu
        DemandeModificationCompteRendu.objects.create(
            compte_rendu=self,
            administrateur=administrateur,
            commentaires=commentaires
        )

# ============================================
# MODÈLE IMAGE_COMPTE_RENDU (OPTION 1 - LÉGER)
# ============================================

class ImageCompteRendu(models.Model):
    """Images associées à un compte rendu"""
    compte_rendu = models.ForeignKey(
        CompteRendu,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Compte rendu"
    )
    
    image = models.ImageField(
        upload_to=image_compte_rendu_path,
        verbose_name="Fichier image",
        validators=[validate_image_size]
    )
    
    legende = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Légende",
        help_text="Description courte de l'image"
    )
    
    ordre = models.IntegerField(
        default=0,
        verbose_name="Ordre d'affichage",
        help_text="Pour organiser l'ordre des images"
    )
    
    date_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'upload"
    )
    
    est_valide = models.BooleanField(
        default=True,
        verbose_name="Image valide",
        help_text="L'image a été vérifiée par l'administration"
    )
    
    class Meta:
        verbose_name = "Image de compte rendu"
        verbose_name_plural = "Images de compte rendu"
        ordering = ['ordre', 'date_upload']
        indexes = [
            models.Index(fields=['compte_rendu', 'ordre']),
            models.Index(fields=['compte_rendu', 'est_valide']),
        ]
    
    def __str__(self):
        return f"Image {self.id} - {self.compte_rendu.titre}"
    
    def save(self, *args, **kwargs):
        """Override save pour gérer l'ordre automatique"""
        if not self.pk and self.ordre == 0:
            dernier = ImageCompteRendu.objects.filter(
                compte_rendu=self.compte_rendu
            ).order_by('-ordre').first()
            self.ordre = (dernier.ordre + 1) if dernier else 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete pour supprimer le fichier physique"""
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)
    
    @property
    def nom_fichier(self):
        """Retourne le nom du fichier sans le chemin"""
        return os.path.basename(self.image.name)
    
    @property
    def extension(self):
        """Retourne l'extension du fichier"""
        return os.path.splitext(self.image.name)[1].lower().replace('.', '')
    
    @property
    def taille_formattee(self):
        """Retourne la taille formatée"""
        try:
            size = self.image.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} GB"
        except:
            return "Inconnue"
    
    def get_absolute_url(self):
        """URL absolue de l'image"""
        return self.image.url
    
    def get_thumbnail_url(self):
        """URL pour une miniature (peut être implémentée plus tard)"""
        return self.image.url  # Pour l'instant, retourne l'image originale
    
    def marquer_comme_invalide(self, motif=""):
        """Marque l'image comme invalide"""
        self.est_valide = False
        self.save()


# Ajouter dans models.py (à la fin du fichier)

class DemandeModificationCompteRendu(models.Model):
    """Modèle pour suivre les demandes de modification sur un compte rendu"""
    compte_rendu = models.ForeignKey(
        CompteRendu,
        on_delete=models.CASCADE,
        related_name='demandes_modification',
        verbose_name="Compte rendu"
    )
    
    administrateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='demandes_modification_faites',
        verbose_name="Administrateur"
    )
    
    commentaires = models.TextField(verbose_name="Commentaires pour modification")
    
    date_demande = models.DateTimeField(default=timezone.now, verbose_name="Date de la demande")
    
    date_modification = models.DateTimeField(null=True, blank=True, verbose_name="Date de modification")
    
    est_resolue = models.BooleanField(default=False, verbose_name="Demande résolue")
    
    class Meta:
        verbose_name = "Demande de modification de compte rendu"
        verbose_name_plural = "Demandes de modification de compte rendu"
        ordering = ['-date_demande']
    
    def __str__(self):
        return f"Modification demandée pour {self.compte_rendu.titre}"
    
    def marquer_comme_resolue(self):
        """Marquer la demande comme résolue"""
        self.est_resolue = True
        self.date_modification = timezone.now()
        self.save()