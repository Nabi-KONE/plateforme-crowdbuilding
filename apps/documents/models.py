"""
Modèles pour la gestion des documents
Plateforme crowdBuilding - Burkina Faso
"""
from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from apps.accounts.models import Utilisateur
from apps.projects.models import Projet
import os


class TypeDocument(models.TextChoices):
    """Types de documents acceptés sur la plateforme"""
    JUSTIFICATIF_IDENTITE = 'JUSTIFICATIF_IDENTITE', 'Justificatif d\'identité'
    JUSTIFICATIF_REVENU = 'JUSTIFICATIF_REVENU', 'Justificatif de revenu'
    JUSTIFICATIF_FONDS = 'JUSTIFICATIF_FONDS', 'Justificatif d\'origine des fonds'
    STATUTS_ENTREPRISE = 'STATUTS_ENTREPRISE', 'Statuts d\'entreprise'  # AJOUTÉ
    DOCUMENT_PROJET = 'DOCUMENT_PROJET', 'Document de projet'
    PLAN_FINANCIER = 'PLAN_FINANCIER', 'Plan financier'
    PIECE_IDENTITE = 'PIECE_IDENTITE', 'Pièce d\'identité'
    CONTRAT_SIGNE = 'CONTRAT_SIGNE', 'Contrat signé'
    RAPPORT_AVANCEMENT = 'RAPPORT_AVANCEMENT', 'Rapport d\'avancement'


class StatutDocument(models.TextChoices):
    """Statuts possibles pour un document"""
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VALIDE = 'VALIDE', 'Validé'
    REFUSE = 'REFUSE', 'Refusé'


def document_upload_path(instance, filename):
    """
    Fonction pour déterminer le chemin d'upload des documents
    Organise les documents par type et par utilisateur/projet
    """
    if instance.proprietaire_type == 'utilisateur':
        return f'documents/utilisateurs/{instance.proprietaire_id}/{instance.type}/{filename}'
    elif instance.proprietaire_type == 'projet':
        return f'documents/projets/{instance.proprietaire_id}/{instance.type}/{filename}'
    else:
        return f'documents/autres/{instance.type}/{filename}'


class Document(models.Model):
    """
    Modèle pour gérer tous les documents de la plateforme
    Peut être associé à un utilisateur ou à un projet
    """
    # Informations de base
    nom = models.CharField(max_length=200, verbose_name="Nom du document")
    type = models.CharField(
        max_length=25,
        choices=TypeDocument.choices,
        verbose_name="Type de document"
    )
    
    # Fichier
    fichier = models.FileField(
        upload_to=document_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif']
            )
        ],
        verbose_name="Fichier"
    )
    taille = models.BigIntegerField(verbose_name="Taille (bytes)")
    
    # Métadonnées
    date_telechargement = models.DateTimeField(default=timezone.now, verbose_name="Date de téléchargement")
    statut = models.CharField(
        max_length=15,
        choices=StatutDocument.choices,
        default=StatutDocument.EN_ATTENTE,
        verbose_name="Statut du document"
    )
    
    # Relations
    proprietaire_id = models.PositiveIntegerField(verbose_name="ID du propriétaire")
    proprietaire_type = models.CharField(
        max_length=15,
        choices=[
            ('utilisateur', 'Utilisateur'),
            ('projet', 'Projet'),
        ],
        verbose_name="Type de propriétaire"
    )
    
    # Validation
    date_validation = models.DateTimeField(null=True, blank=True, verbose_name="Date de validation")
    administrateur_validateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents_valides',
        verbose_name="Administrateur validateur"
    )
    motif_refus = models.TextField(blank=True, verbose_name="Motif de refus")
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-date_telechargement']
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"
    
    def save(self, *args, **kwargs):
        """Override save pour calculer la taille du fichier"""
        if self.fichier and not self.taille:
            try:
                self.taille = self.fichier.size
            except (ValueError, AttributeError):
                self.taille = 0
        
        super().save(*args, **kwargs)
    
    @property
    def taille_mb(self):
        """Retourne la taille en MB"""
        return round(self.taille / (1024 * 1024), 2)
    
    @property
    def extension(self):
        """Retourne l'extension du fichier"""
        if self.fichier:
            return os.path.splitext(self.fichier.name)[1].lower()
        return ''
    
    @property
    def est_image(self):
        """Vérifie si le document est une image"""
        return self.extension in ['.jpg', '.jpeg', '.png', '.gif']
    
    @property
    def est_pdf(self):
        """Vérifie si le document est un PDF"""
        return self.extension == '.pdf'
    
    def valider(self, administrateur):
        """Valide le document"""
        self.statut = StatutDocument.VALIDE
        self.date_validation = timezone.now()
        self.administrateur_validateur = administrateur
        self.motif_refus = ""
        self.save()
    
    def refuser(self, administrateur, motif):
        """Refuse le document avec un motif"""
        self.statut = StatutDocument.REFUSE
        self.administrateur_validateur = administrateur
        self.motif_refus = motif
        self.save()
    
    def telecharger(self):
        """Méthode pour télécharger le document"""
        # Cette méthode pourrait être étendue pour ajouter des logs de téléchargement
        return self.fichier
    
    def get_proprietaire(self):
        """Retourne l'objet propriétaire du document"""
        if self.proprietaire_type == 'utilisateur':
            try:
                return Utilisateur.objects.get(id=self.proprietaire_id)
            except Utilisateur.DoesNotExist:
                return None
        elif self.proprietaire_type == 'projet':
            try:
                return Projet.objects.get(id=self.proprietaire_id)
            except Projet.DoesNotExist:
                return None
        return None
    
    @classmethod
    def get_documents_utilisateur(cls, utilisateur_id):
        """Retourne tous les documents d'un utilisateur"""
        return cls.objects.filter(
            proprietaire_type='utilisateur',
            proprietaire_id=utilisateur_id
        )
    
    @classmethod
    def get_documents_projet(cls, projet_id):
        """Retourne tous les documents d'un projet"""
        return cls.objects.filter(
            proprietaire_type='projet',
            proprietaire_id=projet_id
        )
    
    @classmethod
    def get_documents_en_attente(cls):
        """Retourne tous les documents en attente de validation"""
        return cls.objects.filter(statut=StatutDocument.EN_ATTENTE)
