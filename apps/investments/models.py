"""
Modèles pour la gestion des investissements et transactions
Plateforme crowdBuilding - Burkina Faso
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.accounts.models import Utilisateur
from apps.projects.models import Projet
import uuid


class StatutInvestissement(models.TextChoices):
    """Statuts possibles pour un investissement"""
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    CONFIRME = 'CONFIRME', 'Confirmé'
    ANNULE = 'ANNULE', 'Annulé'


class TypeTransaction(models.TextChoices):
    """Types de transactions"""
    INVESTISSEMENT = 'INVESTISSEMENT', 'Investissement'
    REMBOURSEMENT = 'REMBOURSEMENT', 'Remboursement'
    RENDEMENT = 'RENDEMENT', 'Rendement'


class StatutTransaction(models.TextChoices):
    """Statuts possibles pour une transaction"""
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VALIDEE = 'VALIDEE', 'Validée'
    ECHOUEE = 'ECHOUEE', 'Échouée'
    ANNULEE = 'ANNULEE', 'Annulée'


class Investissement(models.Model):
    """
    Modèle pour les investissements dans les projets
    """
    # Informations de base
    reference = models.CharField(max_length=20, unique=True, verbose_name="Référence")
    investisseur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='investissements',
        verbose_name="Investisseur"
    )
    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='investissements',
        verbose_name="Projet"
    )
    
    # Informations financières
    montant = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(10000)],  # Minimum 10 000 FCFA
        verbose_name="Montant investi (FCFA)"
    )
    
    # Métadonnées
    date_investissement = models.DateTimeField(default=timezone.now, verbose_name="Date d'investissement")
    statut = models.CharField(
        max_length=15,
        choices=StatutInvestissement.choices,
        default=StatutInvestissement.EN_ATTENTE,
        verbose_name="Statut de l'investissement"
    )
    
    # Informations supplémentaires
    origine_fonds = models.CharField(
        max_length=100,
        choices=[
            ('SALAIRE', 'Salaire'),
            ('BUSINESS', 'Activité commerciale'),
            ('HERITAGE', 'Héritage'),
            ('EPARGNE', 'Épargne'),
            ('DIASPORA', 'Fonds de la diaspora'),
            ('AUTRE', 'Autre'),
        ],
        verbose_name="Origine des fonds"
    )
    contrat_accepte = models.BooleanField(default=False, verbose_name="Contrat accepté")
    date_contrat = models.DateTimeField(null=True, blank=True, verbose_name="Date d'acceptation du contrat")
    
    class Meta:
        verbose_name = "Investissement"
        verbose_name_plural = "Investissements"
        ordering = ['-date_investissement']
        unique_together = ['investisseur', 'projet']  # Un investisseur ne peut investir qu'une fois par projet
    
    def __str__(self):
        return f"{self.reference} - {self.investisseur.nom_complet} - {self.projet.titre}"
    
    def save(self, *args, **kwargs):
        """Override save pour générer automatiquement la référence"""
        if not self.reference:
            # Générer une référence unique : INV-YYYY-XXXX
            year = timezone.now().year
            last_investment = Investissement.objects.filter(
                reference__startswith=f'INV-{year}-'
            ).order_by('-reference').first()
            
            if last_investment:
                last_number = int(last_investment.reference.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.reference = f'INV-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    def confirmer(self):
        """Confirme l'investissement"""
        self.statut = StatutInvestissement.CONFIRME
        self.save()
        
        # Mettre à jour le montant collecté du projet
        self.projet.montant_collecte += self.montant
        self.projet.save()
        
        # Vérifier si le projet est entièrement financé
        if self.projet.est_finance_complet:
            self.projet.finaliser_financement()
    
    def annuler(self):
        """Annule l'investissement"""
        self.statut = StatutInvestissement.ANNULE
        self.save()
    
    def calculer_rendement(self):
        """Calcule le rendement attendu de l'investissement"""
        taux_rendement = self.projet.taux_rendement / 100
        return self.montant * taux_rendement
    
    def calculer_rendement_mensuel(self):
        """Calcule le rendement mensuel attendu"""
        rendement_total = self.calculer_rendement()
        duree_mois = self.projet.duree
        return rendement_total / duree_mois if duree_mois > 0 else 0


class Transaction(models.Model):
    """
    Modèle pour toutes les transactions financières
    """
    # Informations de base
    reference = models.CharField(max_length=20, unique=True, verbose_name="Référence")
    investissement = models.ForeignKey(
        Investissement,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="Investissement"
    )
    
    # Informations financières
    montant = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Montant (FCFA)"
    )
    
    # Métadonnées
    date_transaction = models.DateTimeField(default=timezone.now, verbose_name="Date de transaction")
    type = models.CharField(
        max_length=15,
        choices=TypeTransaction.choices,
        verbose_name="Type de transaction"
    )
    statut = models.CharField(
        max_length=15,
        choices=StatutTransaction.choices,
        default=StatutTransaction.EN_ATTENTE,
        verbose_name="Statut de la transaction"
    )
    
    # Informations supplémentaires
    description = models.TextField(blank=True, verbose_name="Description")
    numero_transaction_bancaire = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Numéro de transaction bancaire"
    )
    
    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ['-date_transaction']
    
    def __str__(self):
        return f"{self.reference} - {self.get_type_display()} - {self.montant} FCFA"
    
    def save(self, *args, **kwargs):
        """Override save pour générer automatiquement la référence"""
        if not self.reference:
            # Générer une référence unique : TXN-YYYY-XXXX
            year = timezone.now().year
            last_transaction = Transaction.objects.filter(
                reference__startswith=f'TXN-{year}-'
            ).order_by('-reference').first()
            
            if last_transaction:
                last_number = int(last_transaction.reference.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.reference = f'TXN-{year}-{new_number:04d}'
        
        super().save(*args, **kwargs)
    
    def valider(self):
        """Valide la transaction"""
        self.statut = StatutTransaction.VALIDEE
        self.save()
        
        # Si c'est un investissement, confirmer l'investissement
        if self.type == TypeTransaction.INVESTISSEMENT:
            self.investissement.confirmer()
    
    def annuler(self):
        """Annule la transaction"""
        self.statut = StatutTransaction.ANNULEE
        self.save()
    
    def marquer_echouee(self):
        """Marque la transaction comme échouée"""
        self.statut = StatutTransaction.ECHOUEE
        self.save()
    
    @property
    def est_validee(self):
        """Vérifie si la transaction est validée"""
        return self.statut == StatutTransaction.VALIDEE
    
    @property
    def est_en_attente(self):
        """Vérifie si la transaction est en attente"""
        return self.statut == StatutTransaction.EN_ATTENTE
