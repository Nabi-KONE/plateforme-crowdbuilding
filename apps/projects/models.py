"""
Modèles pour la gestion des projets immobiliers
Plateforme crowdBuilding - Burkina Faso
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.accounts.models import Utilisateur
import uuid


class StatutProjet(models.TextChoices):
    """Statuts possibles pour un projet"""
    EN_ATTENTE_VALIDATION = 'EN_ATTENTE_VALIDATION', 'En attente de validation'
    VALIDE = 'VALIDE', 'Validé'
    REFUSE = 'REFUSE', 'Refusé'
    EN_COURS_FINANCEMENT = 'EN_COURS_FINANCEMENT', 'En cours de financement'
    FINANCE = 'FINANCE', 'Financé'
    EN_REALISATION = 'EN_REALISATION', 'En réalisation'
    TERMINE = 'TERMINE', 'Terminé'
    ANNULE = 'ANNULE', 'Annulé'


class Projet(models.Model):
    """
    Modèle pour les projets immobiliers
    Un promoteur peut soumettre un projet pour le financement participatif
    """
    # Informations de base
    reference = models.CharField(max_length=20, unique=True, verbose_name="Référence")
    titre = models.CharField(max_length=200, verbose_name="Titre du projet")
    description = models.TextField(verbose_name="Description détaillée")
    
    # Informations financières
    taux_rendement = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(100)],
        verbose_name="Taux de rendement (%)"
    )
    montant_total = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(100000)],  # Minimum 100 000 FCFA
        verbose_name="Montant total (FCFA)"
    )
    montant_collecte = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=0,
        verbose_name="Montant collecté (FCFA)"
    )
    
    # Informations temporelles
    duree = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)],  # 1 à 60 mois
        verbose_name="Durée (mois)"
    )
    date_debut = models.DateField(verbose_name="Date de début prévue")
    date_fin = models.DateField(verbose_name="Date de fin prévue")
    
    # Localisation
    localisation = models.CharField(max_length=200, verbose_name="Localisation")
    ville = models.CharField(max_length=100, default="Ouagadougou", verbose_name="Ville")
    region = models.CharField(max_length=100, default="Centre", verbose_name="Région")
    
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
                reference__startswith=f'PROJ-{year}-'
            ).order_by('-reference').first()
            
            if last_project:
                last_number = int(last_project.reference.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.reference = f'PROJ-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
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
    
    @property
    def est_financeable(self):
        """Vérifie si le projet peut recevoir des investissements"""
        return self.statut in [
            StatutProjet.VALIDE,
            StatutProjet.EN_COURS_FINANCEMENT,
            StatutProjet.FINANCE
        ]
    
    def calculer_taux_financement(self):
        """Méthode pour calculer le taux de financement"""
        return self.taux_financement
    
    def verifier_disponibilite(self):
        """Vérifie si le projet peut encore recevoir des investissements"""
        return self.est_financeable and not self.est_finance_complet
    
    def publier(self):
        """Publie le projet (le rend visible et financeable)"""
        if self.statut == StatutProjet.EN_ATTENTE_VALIDATION:
            self.statut = StatutProjet.VALIDE
            self.date_validation = timezone.now()
            self.save()
    
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
    
    def commencer_financement(self):
        """Démarre la phase de financement"""
        if self.statut == StatutProjet.VALIDE:
            self.statut = StatutProjet.EN_COURS_FINANCEMENT
            self.save()
    
    def finaliser_financement(self):
        """Finalise le financement du projet"""
        if self.statut == StatutProjet.EN_COURS_FINANCEMENT:
            self.statut = StatutProjet.FINANCE
            self.save()
    
    def commencer_realisation(self):
        """Démarre la phase de réalisation"""
        if self.statut == StatutProjet.FINANCE:
            self.statut = StatutProjet.EN_REALISATION
            self.save()
    
    def terminer(self):
        """Termine le projet"""
        if self.statut == StatutProjet.EN_REALISATION:
            self.statut = StatutProjet.TERMINE
            self.save()
    
    def annuler(self):
        """Annule le projet"""
        self.statut = StatutProjet.ANNULE
        self.save()


class Etape(models.Model):
    """
    Modèle pour les étapes de réalisation d'un projet
    """
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='etapes',
        verbose_name="Projet"
    )
    titre = models.CharField(max_length=200, verbose_name="Titre de l'étape")
    description = models.TextField(verbose_name="Description")
    ordre = models.IntegerField(verbose_name="Ordre")
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
    
    def valider(self):
        """Valide l'étape"""
        self.terminee = True
        self.date_realisation = timezone.now()
        self.save()


class CompteRendu(models.Model):
    """
    Modèle pour les comptes rendus de projet
    """
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='comptes_rendus',
        verbose_name="Projet"
    )
    titre = models.CharField(max_length=200, verbose_name="Titre")
    contenu = models.TextField(verbose_name="Contenu")
    date_publication = models.DateTimeField(default=timezone.now, verbose_name="Date de publication")
    avancement = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        verbose_name="Avancement (%)"
    )
    
    class Meta:
        verbose_name = "Compte rendu"
        verbose_name_plural = "Comptes rendus"
        ordering = ['-date_publication']
    
    def __str__(self):
        return f"{self.projet.titre} - {self.titre}"
    
    def publier(self):
        """Publie le compte rendu"""
        # Ici on pourrait ajouter des vérifications ou notifications
        self.save()
