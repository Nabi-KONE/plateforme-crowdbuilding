"""
Modèles pour la gestion des investissements et transactions
Plateforme crowdBuilding - Burkina Faso
"""

from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator
from apps.accounts.models import Utilisateur
from apps.projects.models import Projet
from django.db import transaction as db_transaction
from django.db import transaction




# =========================
# ENUMS / STATUTS
# =========================

class StatutInvestissement(models.TextChoices):
    EN_ATTENTE_PAIEMENT = 'EN_ATTENTE_PAIEMENT', 'En attente de paiement'
    PAIEMENT_RECU = 'PAIEMENT_RECU', 'Paiement reçu'
    CONFIRME = 'CONFIRME', 'Confirmé par admin'
    REJETE = 'REJETE', 'Rejeté'
    ANNULE = 'ANNULE', 'Annulé'
    REMBOURSE = 'REMBOURSE', 'Remboursé'


class TypeTransaction(models.TextChoices):
    INVESTISSEMENT = 'INVESTISSEMENT', 'Investissement'
    REMBOURSEMENT = 'REMBOURSEMENT', 'Remboursement'


class StatutTransaction(models.TextChoices):
    EN_ATTENTE = 'EN_ATTENTE', 'En attente'
    VALIDEE = 'VALIDEE', 'Validée'
    ECHOUEE = 'ECHOUEE', 'Échouée'
    ANNULEE = 'ANNULEE', 'Annulée'


# =========================
# INVESTISSEMENT
# =========================

class Investissement(models.Model):

    reference = models.CharField(max_length=20, unique=True, verbose_name="Référence")

    investisseur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='investissements'
    )

    projet = models.ForeignKey(
        Projet,
        on_delete=models.CASCADE,
        related_name='investissements'
    )

    nombre_parts = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Nombre de parts détenues"
    )

    montant = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(10000)],
        verbose_name="Montant investi (FCFA)"
    )

    date_investissement = models.DateTimeField(default=timezone.now)

    statut = models.CharField(
        max_length=30,
        choices=StatutInvestissement.choices,
        default=StatutInvestissement.EN_ATTENTE_PAIEMENT
    )

    origine_fonds = models.CharField(
        max_length=100,
        choices=[
            ('SALAIRE', 'Salaire'),
            ('BUSINESS', 'Activité commerciale'),
            ('HERITAGE', 'Héritage'),
            ('EPARGNE', 'Épargne'),
            ('DIASPORA', 'Fonds de la diaspora'),
            ('AUTRE', 'Autre'),
        ]
    )

    contrat_accepte = models.BooleanField(default=False)
    date_contrat = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_investissement']

    def __str__(self):
        return f"{self.reference} - {self.investisseur} - {self.projet}"

  
    def save(self, *args, **kwargs):
        if not self.reference:
            with transaction.atomic():
                year = timezone.now().year
                last = Investissement.objects.select_for_update().filter(
                    reference__startswith=f'INV-{year}-'
                ).order_by('-reference').first()
                number = int(last.reference.split('-')[-1]) + 1 if last else 1
                self.reference = f'INV-{year}-{number:04d}'

        self.full_clean()
        super().save(*args, **kwargs)




    # =========================
    # ACTIONS METIER (ADMIN)
    # =========================

    def confirmer_par_admin(self):
        if self.statut != StatutInvestissement.PAIEMENT_RECU.value:
            raise ValueError("Paiement non reçu")

        self.statut = StatutInvestissement.CONFIRME.value
        self.save()

        # Mise à jour projet
        projet = self.projet
        projet.montant_collecte += self.montant
        projet.parts_vendues += self.nombre_parts
        projet.save()

        # Finalisation automatique si 100%
        projet.finaliser_financement()
        


    def rejeter_avec_remboursement(self, raison=""):
        """
        Rejet administratif avec remboursement si paiement déjà reçu
        """
        if self.statut not in [
            StatutInvestissement.PAIEMENT_RECU.value,
            StatutInvestissement.EN_ATTENTE_PAIEMENT.value
        ]:
            raise ValueError("Impossible de rejeter cet investissement dans son état actuel.")

        with db_transaction.atomic():

            # Paiement déjà reçu → remboursement
            if self.statut == StatutInvestissement.PAIEMENT_RECU.value:
                Transaction.objects.create(
                    investissement=self,
                    montant=self.montant,
                    type=TypeTransaction.REMBOURSEMENT,
                    statut=StatutTransaction.VALIDEE,
                    description=f"Remboursement automatique suite rejet : {raison}"
                )
                self.statut = StatutInvestissement.REMBOURSE.value

            # Jamais payé → simple rejet
            else:
                self.statut = StatutInvestissement.REJETE.value

            self.save()


    def annuler(self):
        self.statut = StatutInvestissement.ANNULE.value
        self.save()
    
    def clean(self):
        if self.nombre_parts < self.projet.nombre_min_parts:
            raise ValidationError(
                f"Minimum requis : {self.projet.nombre_min_parts} parts."
            )

    


# =========================
# TRANSACTION
# =========================

class Transaction(models.Model):

    reference = models.CharField(max_length=20, unique=True)

    investissement = models.ForeignKey(
        Investissement,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    montant = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    date_transaction = models.DateTimeField(default=timezone.now)

    type = models.CharField(max_length=20, choices=TypeTransaction.choices)
    statut = models.CharField(
        max_length=20,
        choices=StatutTransaction.choices,
        default=StatutTransaction.EN_ATTENTE
    )

    mode_paiement = models.CharField(
        max_length=20,
        choices=[
            ('ORANGE_MONEY', 'Orange Money'),
            ('MOOV_MONEY', 'Moov Money'),
            ('WAVE', 'Wave'),
            ('CARTE_BANCAIRE', 'Carte Bancaire'),
            ('VIREMENT', 'Virement Bancaire'),
        ],
        blank=True
    )

    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-date_transaction']

    def __str__(self):
        return f"{self.reference} - {self.montant} FCFA"

    def save(self, *args, **kwargs):
        if not self.reference:
            year = timezone.now().year
            last = Transaction.objects.filter(
                reference__startswith=f'TXN-{year}-'
            ).order_by('-reference').first()
            number = int(last.reference.split('-')[-1]) + 1 if last else 1
            self.reference = f'TXN-{year}-{number:04d}'
        super().save(*args, **kwargs)

    def valider_paiement(self):
        """
        Paiement validé (admin ou webhook)
        """
        if self.statut == StatutTransaction.VALIDEE:
            return

        if self.investissement.statut != StatutInvestissement.EN_ATTENTE_PAIEMENT.value:
            raise ValueError("Impossible de valider ce paiement")

        self.statut = StatutTransaction.VALIDEE.value
        self.save()

        self.investissement.statut = StatutInvestissement.PAIEMENT_RECU.value
        self.investissement.save()
