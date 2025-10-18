"""
Configuration de l'interface d'administration Django
Module investments - Plateforme crowdBuilding
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Investissement, Transaction


@admin.register(Investissement)
class InvestissementAdmin(admin.ModelAdmin):
    """
    Administration des investissements
    """
    list_display = ('reference', 'investisseur', 'projet', 'montant', 'statut', 'date_investissement', 'rendement_attendu')
    list_filter = ('statut', 'origine_fonds', 'date_investissement', 'contrat_accepte')
    search_fields = ('reference', 'investisseur__nom', 'investisseur__prenom', 'projet__titre')
    ordering = ('-date_investissement',)
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('reference', 'investisseur', 'projet')
        }),
        ('Informations financières', {
            'fields': ('montant', 'origine_fonds')
        }),
        ('Statut et contrat', {
            'fields': ('statut', 'contrat_accepte', 'date_contrat')
        }),
        ('Dates', {
            'fields': ('date_investissement',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('reference', 'date_investissement')
    
    actions = ['confirmer_investissements', 'annuler_investissements']
    
    def rendement_attendu(self, obj):
        """Afficher le rendement attendu"""
        rendement = obj.calculer_rendement()
        return f"{rendement:,.0f} FCFA"
    rendement_attendu.short_description = 'Rendement attendu'
    
    def confirmer_investissements(self, request, queryset):
        """Action pour confirmer plusieurs investissements"""
        count = 0
        for investissement in queryset.filter(statut='EN_ATTENTE'):
            investissement.confirmer()
            count += 1
        
        self.message_user(request, f'{count} investissement(s) confirmé(s) avec succès.')
    confirmer_investissements.short_description = "Confirmer les investissements sélectionnés"
    
    def annuler_investissements(self, request, queryset):
        """Action pour annuler plusieurs investissements"""
        count = 0
        for investissement in queryset.filter(statut__in=['EN_ATTENTE', 'CONFIRME']):
            investissement.annuler()
            count += 1
        
        self.message_user(request, f'{count} investissement(s) annulé(s).')
    annuler_investissements.short_description = "Annuler les investissements sélectionnés"


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Administration des transactions
    """
    list_display = ('reference', 'investissement', 'type', 'montant', 'statut', 'date_transaction')
    list_filter = ('type', 'statut', 'date_transaction')
    search_fields = ('reference', 'investissement__reference', 'numero_transaction_bancaire')
    ordering = ('-date_transaction',)
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('reference', 'investissement', 'type')
        }),
        ('Informations financières', {
            'fields': ('montant', 'numero_transaction_bancaire')
        }),
        ('Statut et description', {
            'fields': ('statut', 'description')
        }),
        ('Dates', {
            'fields': ('date_transaction',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('reference', 'date_transaction')
    
    actions = ['valider_transactions', 'annuler_transactions']
    
    def valider_transactions(self, request, queryset):
        """Action pour valider plusieurs transactions"""
        count = 0
        for transaction in queryset.filter(statut='EN_ATTENTE'):
            transaction.valider()
            count += 1
        
        self.message_user(request, f'{count} transaction(s) validée(s) avec succès.')
    valider_transactions.short_description = "Valider les transactions sélectionnées"
    
    def annuler_transactions(self, request, queryset):
        """Action pour annuler plusieurs transactions"""
        count = 0
        for transaction in queryset.filter(statut__in=['EN_ATTENTE', 'VALIDEE']):
            transaction.annuler()
            count += 1
        
        self.message_user(request, f'{count} transaction(s) annulée(s).')
    annuler_transactions.short_description = "Annuler les transactions sélectionnées"
