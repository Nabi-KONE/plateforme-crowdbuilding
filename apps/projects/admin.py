"""
Configuration de l'interface d'administration Django
Module projects - Plateforme crowdBuilding
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Projet, Etape, CompteRendu, ImageProjet, DocumentProjet

class ImageProjetInline(admin.TabularInline):
    """Inline pour les images du projet"""
    model = ImageProjet
    extra = 1
    fields = ['image', 'legende', 'est_principale', 'date_ajout']
    readonly_fields = ['date_ajout']

class DocumentProjetInline(admin.TabularInline):
    """Inline pour les documents du projet"""
    model = DocumentProjet
    extra = 1
    fields = ['type_document', 'nom', 'fichier', 'est_public', 'date_ajout']
    readonly_fields = ['date_ajout']

class EtapeInline(admin.TabularInline):
    """Inline pour les étapes du projet"""
    model = Etape
    extra = 1
    fields = ['titre', 'ordre', 'date_debut', 'duree_estimee', 'terminee', 'date_realisation']  # ⚠️ CHANGER ICI

class CompteRenduInline(admin.TabularInline):
    """Inline pour les comptes rendus du projet"""
    model = CompteRendu
    extra = 1
    fields = ['titre', 'avancement', 'date_publication']

@admin.register(Projet)
class ProjetAdmin(admin.ModelAdmin):
    """
    Administration des projets
    """
    list_display = ('reference', 'titre', 'promoteur', 'statut', 'etapes_definies', 'taux_financement', 'montant_total', 'date_creation')
    list_filter = ('statut', 'ville', 'region', 'etapes_definies', 'date_creation', 'date_debut')
    search_fields = ('reference', 'titre', 'promoteur__nom', 'promoteur__prenom', 'localisation')
    ordering = ('-date_creation',)
    
    inlines = [ImageProjetInline, DocumentProjetInline, EtapeInline, CompteRenduInline]
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'titre', 'resume', 'description', 'promoteur', 'etapes_definies')
        }),
        ('Informations financières', {
            'fields': ('montant_total', 'montant_collecte', 'montant_min_investissement')
        }),
        ('Informations temporelles', {
            'fields': ('duree', 'date_debut', 'date_fin', 'date_debut_execution')
        }),
        ('Localisation', {
            'fields': ('localisation', 'ville', 'region', 'adresse_complete')
        }),
        ('Statut et validation', {
            'fields': ('statut', 'date_validation', 'administrateur_validateur', 'motif_refus')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_publication'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('reference', 'date_creation', 'taux_financement')
    
    actions = ['valider_projets', 'completer_projets', 'refuser_projets', 'lancer_campagne']
    
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
        '<span style="color: {};">{}%</span>',
        color,
        "{:.1f}".format(float(taux))  # Formater le taux avant
    )
    taux_financement.short_description = 'Financement'
    
    def valider_projets(self, request, queryset):
        """Action pour valider plusieurs projets"""
        count = 0
        for projet in queryset.filter(statut__in=['EN_ATTENTE_VALIDATION', 'A_COMPLETER']):
            projet.valider(request.user)
            projet.lancer_campagne()
            count += 1
        
        self.message_user(request, f'{count} projet(s) validé(s) avec succès.')
    valider_projets.short_description = "Valider les projets sélectionnés"
    
    def completer_projets(self, request, queryset):
        """Action pour renvoyer des projets pour complément"""
        count = 0
        for projet in queryset.filter(statut='EN_ATTENTE_VALIDATION'):
            projet.statut = 'A_COMPLETER'
            projet.motif_refus = "Merci de préciser au moins les grandes étapes avant validation."
            projet.save()
            count += 1
        
        self.message_user(request, f'{count} projet(s) renvoyé(s) pour complément.')
    completer_projets.short_description = "Renvoyer pour complément"
    
    def refuser_projets(self, request, queryset):
        """Action pour refuser plusieurs projets"""
        count = 0
        for projet in queryset.filter(statut='EN_ATTENTE_VALIDATION'):
            projet.refuser(request.user, 'Refusé par action groupée')
            count += 1
        
        self.message_user(request, f'{count} projet(s) refusé(s).')
    refuser_projets.short_description = "Refuser les projets sélectionnés"
    
    def lancer_campagne(self, request, queryset):
        """Action pour lancer la campagne de plusieurs projets"""
        count = 0
        for projet in queryset.filter(statut='VALIDE'):
            projet.lancer_campagne()
            count += 1
        
        self.message_user(request, f'{count} projet(s) mis en campagne.')
    lancer_campagne.short_description = "Lancer la campagne"

@admin.register(Etape)
class EtapeAdmin(admin.ModelAdmin):
    """
    Administration des étapes de projet
    """
    list_display = ('projet', 'titre', 'ordre', 'date_debut', 'duree_estimee', 'terminee', 'date_publication')  # ⚠️ CHANGER ICI
    list_filter = ('terminee', 'date_publication', 'projet__statut')
    search_fields = ('projet__titre', 'titre', 'description')
    ordering = ('projet', 'ordre')
    
    fieldsets = (
        ('Informations de l\'étape', {
            'fields': ('projet', 'titre', 'description', 'ordre', 'date_debut', 'duree_estimee')  # ⚠️ CHANGER ICI
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
    
    # Optionnel : Ajouter une colonne pour la date de fin calculée
    def date_fin_calculee(self, obj):
        return obj.date_fin  # Utilise la propriété du modèle
    date_fin_calculee.short_description = 'Date de fin (calculée)'

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