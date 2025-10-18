"""
Configuration de l'interface d'administration Django
Module projects - Plateforme crowdBuilding
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Projet, Etape, CompteRendu


@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    """
    Administration des projets
    """
    list_display = ('reference', 'titre', 'promoteur', 'statut', 'taux_financement', 'montant_total', 'date_creation')
    list_filter = ('statut', 'ville', 'region', 'date_creation', 'date_debut')
    search_fields = ('reference', 'titre', 'promoteur__nom', 'promoteur__prenom', 'localisation')
    ordering = ('-date_creation',)
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'titre', 'description', 'promoteur')
        }),
        ('Informations financières', {
            'fields': ('taux_rendement', 'montant_total', 'montant_collecte')
        }),
        ('Informations temporelles', {
            'fields': ('duree', 'date_debut', 'date_fin')
        }),
        ('Localisation', {
            'fields': ('localisation', 'ville', 'region')
        }),
        ('Statut et validation', {
            'fields': ('statut', 'date_validation', 'administrateur_validateur', 'motif_refus')
        }),
        ('Dates', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('reference', 'date_creation', 'taux_financement')
    
    actions = ['valider_projets', 'refuser_projets', 'commencer_financement']
    
    def taux_financement(self, obj):
        """Afficher le taux de financement"""
        taux = obj.taux_financement
        if taux >= 100:
            color = 'green'
        elif taux >= 50:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            taux
        )
    taux_financement.short_description = 'Financement'
    
    def valider_projets(self, request, queryset):
        """Action pour valider plusieurs projets"""
        count = 0
        for projet in queryset.filter(statut='EN_ATTENTE_VALIDATION'):
            projet.valider(request.user)
            count += 1
        
        self.message_user(request, f'{count} projet(s) validé(s) avec succès.')
    valider_projets.short_description = "Valider les projets sélectionnés"
    
    def refuser_projets(self, request, queryset):
        """Action pour refuser plusieurs projets"""
        count = 0
        for projet in queryset.filter(statut='EN_ATTENTE_VALIDATION'):
            projet.refuser(request.user, 'Refusé par action groupée')
            count += 1
        
        self.message_user(request, f'{count} projet(s) refusé(s).')
    refuser_projets.short_description = "Refuser les projets sélectionnés"
    
    def commencer_financement(self, request, queryset):
        """Action pour commencer le financement de plusieurs projets"""
        count = 0
        for projet in queryset.filter(statut='VALIDE'):
            projet.commencer_financement()
            count += 1
        
        self.message_user(request, f'{count} projet(s) mis en financement.')
    commencer_financement.short_description = "Commencer le financement"


@admin.register(Etape)
class EtapeAdmin(admin.ModelAdmin):
    """
    Administration des étapes de projet
    """
    list_display = ('projet', 'titre', 'ordre', 'terminee', 'date_publication')
    list_filter = ('terminee', 'date_publication', 'projet__statut')
    search_fields = ('projet__titre', 'titre', 'description')
    ordering = ('projet', 'ordre')
    
    fieldsets = (
        ('Informations de l\'étape', {
            'fields': ('projet', 'titre', 'description', 'ordre')
        }),
        ('Statut', {
            'fields': ('terminee', 'date_realisation')
        }),
        ('Dates', {
            'fields': ('date_publication',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_publication',)
    
    actions = ['valider_etapes']
    
    def valider_etapes(self, request, queryset):
        """Action pour valider plusieurs étapes"""
        count = 0
        for etape in queryset.filter(terminee=False):
            etape.valider()
            count += 1
        
        self.message_user(request, f'{count} étape(s) validée(s) avec succès.')
    valider_etapes.short_description = "Valider les étapes sélectionnées"


@admin.register(CompteRendu)
class CompteRenduAdmin(admin.ModelAdmin):
    """
    Administration des comptes rendus
    """
    list_display = ('projet', 'titre', 'avancement', 'date_publication')
    list_filter = ('date_publication', 'projet__statut')
    search_fields = ('projet__titre', 'titre', 'contenu')
    ordering = ('-date_publication',)
    
    fieldsets = (
        ('Informations du compte rendu', {
            'fields': ('projet', 'titre', 'contenu')
        }),
        ('Avancement', {
            'fields': ('avancement',)
        }),
        ('Dates', {
            'fields': ('date_publication',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_publication',)
