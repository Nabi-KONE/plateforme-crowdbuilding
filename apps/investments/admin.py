"""
Configuration de l'interface d'administration Django
Module investments - Plateforme crowdBuilding
"""

from django.contrib import admin
from django.contrib import messages
from .models import (
    Investissement,
    Transaction,
    StatutInvestissement,
    StatutTransaction
)


# ==================================================
# ADMIN INVESTISSEMENT
# ==================================================

@admin.register(Investissement)
class InvestissementAdmin(admin.ModelAdmin):

    list_display = (
        'reference',
        'investisseur',
        'projet',
        'nombre_parts',
        'montant',
        'statut',
        'date_investissement'
    )

    list_filter = (
        'statut',
        'origine_fonds',
        'date_investissement',
        'contrat_accepte'
    )

    search_fields = (
        'reference',
        'investisseur__nom',
        'investisseur__prenom',
        'projet__titre'
    )

    ordering = ('-date_investissement',)

    readonly_fields = (
        'reference',
        'date_investissement'
    )

    fieldsets = (
        ('Informations générales', {
            'fields': (
                'reference',
                'investisseur',
                'projet',
                'statut'
            )
        }),
        ('Détails financiers', {
            'fields': (
                'nombre_parts',
                'montant',
                'origine_fonds'
            )
        }),
        ('Contrat', {
            'fields': (
                'contrat_accepte',
                'date_contrat'
            )
        }),
        ('Dates', {
            'fields': ('date_investissement',),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'confirmer_investissements',
        'rejeter_investissements'
    ]

    # ===============================
    # ACTIONS ADMIN
    # ===============================

    @admin.action(description="Confirmer les investissements (paiement reçu)")
    def confirmer_investissements(self, request, queryset):
        count = 0

        for investissement in queryset.filter(
            statut__in=[
                StatutInvestissement.PAIEMENT_RECU,
                StatutInvestissement.EN_ATTENTE_PAIEMENT
            ]
        ):
            investissement.confirmer_par_admin()
            count += 1

        self.message_user(
            request,
            f"{count} investissement(s) confirmé(s) avec succès.",
            level=messages.SUCCESS
        )

    @admin.action(description="Rejeter les investissements sélectionnés")
    def rejeter_investissements(self, request, queryset):
        count = 0

        for investissement in queryset.exclude(
            statut=StatutInvestissement.CONFIRME
        ):
            investissement.rejeter()
            count += 1

        self.message_user(
            request,
            f"{count} investissement(s) rejeté(s).",
            level=messages.WARNING
        )


# ==================================================
# ADMIN TRANSACTION
# ==================================================

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):

    list_display = (
        'reference',
        'investissement',
        'type',
        'montant',
        'mode_paiement',
        'statut',
        'date_transaction'
    )

    list_filter = (
        'type',
        'statut',
        'mode_paiement',
        'date_transaction'
    )

    search_fields = (
        'reference',
        'investissement__reference'
    )

    ordering = ('-date_transaction',)

    readonly_fields = (
        'reference',
        'date_transaction'
    )

    fieldsets = (
        ('Transaction', {
            'fields': (
                'reference',
                'investissement',
                'type',
                'statut'
            )
        }),
        ('Paiement', {
            'fields': (
                'montant',
                'mode_paiement',
                'description'
            )
        }),
        ('Dates', {
            'fields': ('date_transaction',),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'valider_paiements',
        'annuler_transactions'
    ]

    @admin.action(description="Valider les paiements sélectionnés")
    def valider_paiements(self, request, queryset):
        count = 0

        for transaction in queryset.filter(
            statut=StatutTransaction.EN_ATTENTE
        ):
            transaction.valider_paiement()
            count += 1

        self.message_user(
            request,
            f"{count} paiement(s) validé(s).",
            level=messages.SUCCESS
        )

    @admin.action(description="Annuler les transactions sélectionnées")
    def annuler_transactions(self, request, queryset):
        count = 0

        for transaction in queryset.exclude(
            statut=StatutTransaction.ANNULEE
        ):
            transaction.annuler()
            count += 1

        self.message_user(
            request,
            f"{count} transaction(s) annulée(s).",
            level=messages.WARNING
        )
