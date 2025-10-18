"""
Configuration de l'interface d'administration Django
Module documents - Plateforme crowdBuilding
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    Administration des documents
    """
    list_display = ('nom', 'type', 'proprietaire_info', 'statut', 'taille_mb', 'date_telechargement')
    list_filter = ('type', 'statut', 'proprietaire_type', 'date_telechargement')
    search_fields = ('nom', 'proprietaire_id')
    ordering = ('-date_telechargement',)
    
    fieldsets = (
        ('Informations du document', {
            'fields': ('nom', 'type', 'fichier', 'taille')
        }),
        ('Propriétaire', {
            'fields': ('proprietaire_type', 'proprietaire_id')
        }),
        ('Statut et validation', {
            'fields': ('statut', 'date_validation', 'administrateur_validateur', 'motif_refus')
        }),
        ('Dates', {
            'fields': ('date_telechargement',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('taille', 'date_telechargement')
    
    actions = ['valider_documents', 'refuser_documents']
    
    def proprietaire_info(self, obj):
        """Afficher les informations du propriétaire"""
        proprietaire = obj.get_proprietaire()
        if proprietaire:
            if obj.proprietaire_type == 'utilisateur':
                return f"Utilisateur: {proprietaire.nom_complet}"
            elif obj.proprietaire_type == 'projet':
                return f"Projet: {proprietaire.titre}"
        return f"ID: {obj.proprietaire_id}"
    proprietaire_info.short_description = 'Propriétaire'
    
    def taille_mb(self, obj):
        """Afficher la taille en MB"""
        return f"{obj.taille_mb} MB"
    taille_mb.short_description = 'Taille'
    
    def valider_documents(self, request, queryset):
        """Action pour valider plusieurs documents"""
        count = 0
        for document in queryset.filter(statut='EN_ATTENTE'):
            document.valider(request.user)
            count += 1
        
        self.message_user(request, f'{count} document(s) validé(s) avec succès.')
    valider_documents.short_description = "Valider les documents sélectionnés"
    
    def refuser_documents(self, request, queryset):
        """Action pour refuser plusieurs documents"""
        count = 0
        for document in queryset.filter(statut='EN_ATTENTE'):
            document.refuser(request.user, 'Refusé par action groupée')
            count += 1
        
        self.message_user(request, f'{count} document(s) refusé(s).')
    refuser_documents.short_description = "Refuser les documents sélectionnés"
