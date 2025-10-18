"""
Configuration de l'interface d'administration Django
Module notifications - Plateforme crowdBuilding
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Administration des notifications
    """
    list_display = ('utilisateur', 'titre', 'type', 'lue', 'date_creation', 'action_requise')
    list_filter = ('type', 'lue', 'action_requise', 'date_creation')
    search_fields = ('utilisateur__nom', 'utilisateur__prenom', 'titre', 'contenu')
    ordering = ('-date_creation',)
    
    fieldsets = (
        ('Destinataire', {
            'fields': ('utilisateur',)
        }),
        ('Contenu', {
            'fields': ('titre', 'contenu', 'type')
        }),
        ('Statut', {
            'fields': ('lue', 'date_lecture')
        }),
        ('Relations', {
            'fields': ('projet', 'investissement'),
            'classes': ('collapse',)
        }),
        ('Action', {
            'fields': ('action_requise', 'lien_action'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation', 'date_lecture')
    
    actions = ['marquer_comme_lues', 'envoyer_notifications']
    
    def marquer_comme_lues(self, request, queryset):
        """Action pour marquer plusieurs notifications comme lues"""
        count = 0
        for notification in queryset.filter(lue=False):
            notification.marquer_comme_lue()
            count += 1
        
        self.message_user(request, f'{count} notification(s) marquée(s) comme lue(s).')
    marquer_comme_lues.short_description = "Marquer comme lues"
    
    def envoyer_notifications(self, request, queryset):
        """Action pour renvoyer plusieurs notifications"""
        count = 0
        for notification in queryset:
            notification.envoyer()
            count += 1
        
        self.message_user(request, f'{count} notification(s) envoyée(s).')
    envoyer_notifications.short_description = "Envoyer les notifications"
