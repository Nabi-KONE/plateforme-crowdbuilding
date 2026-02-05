"""
Configuration de l'interface d'administration Django
Module accounts - Plateforme crowdBuilding
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import Utilisateur, Role


@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    """
    Administration des utilisateurs personnalisée
    """
    list_display = ('email', 'nom_complet', 'telephone', 'statut_compte', 'date_inscription', 'get_role_actif')
    list_filter = ('statut_compte', 'date_inscription', 'is_active', 'is_staff')
    search_fields = ('email', 'nom', 'prenom', 'telephone')
    ordering = ('-date_inscription',)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('prenom', 'nom', 'email', 'telephone')
        }),
        ('Informations professionnelles', {
            'fields': ('profession', 'entreprise', 'experience'),
            'classes': ('collapse',)
        }),
        ('Statut du compte', {
            'fields': ('statut_compte', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Dates importantes', {
            'fields': ('date_inscription', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        ('Informations de base', {
            'classes': ('wide',),
            'fields': ('prenom', 'nom', 'email', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ('date_inscription', 'last_login')
    
    def get_role_actif(self, obj):
        """Afficher le rôle actif de l'utilisateur"""
        try:
            # CORRECTION : Utiliser directement la relation roles
            role_actif = obj.roles.filter(role_actif=True).first()
            if role_actif:
                color = 'green' if role_actif.statut == 'VALIDE' else 'orange'
                return format_html(
                    '<span style="color: {};">{}</span>',
                    color,
                    f"{role_actif.get_type_display()} ({role_actif.get_statut_display()})"
                )
            return 'Aucun rôle'
        except Exception as e:
            return f"Erreur: {str(e)}"
    
    get_role_actif.short_description = 'Rôle actif'
    get_role_actif.admin_order_field = 'roles__type'


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """
    Administration des rôles
    """
    list_display = ('utilisateur', 'type', 'statut', 'role_actif', 'date_creation')
    list_filter = ('type', 'statut', 'role_actif', 'date_creation')
    search_fields = ('utilisateur__nom', 'utilisateur__prenom', 'utilisateur__email')
    ordering = ('-date_creation',)
    
    fieldsets = (
        ('Informations du rôle', {
            'fields': ('utilisateur', 'type', 'statut', 'role_actif')
        }),
        ('Dates', {
            'fields': ('date_creation',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation',)
    
    actions = ['valider_roles', 'refuser_roles', 'suspendre_roles']
    
    def valider_roles(self, request, queryset):
        """Action pour valider plusieurs rôles"""
        count = 0
        for role in queryset.filter(statut='EN_ATTENTE_VALIDATION'):
            role.statut = 'VALIDE'
            role.save()
            count += 1
        
        self.message_user(request, f'{count} rôle(s) validé(s) avec succès.')
    valider_roles.short_description = "Valider les rôles sélectionnés"
    
    def refuser_roles(self, request, queryset):
        """Action pour refuser plusieurs rôles"""
        count = 0
        for role in queryset.filter(statut='EN_ATTENTE_VALIDATION'):
            role.statut = 'REFUSE'
            role.save()
            count += 1
        
        self.message_user(request, f'{count} rôle(s) refusé(s).')
    refuser_roles.short_description = "Refuser les rôles sélectionnés"
    
    def suspendre_roles(self, request, queryset):
        """Action pour suspendre plusieurs rôles"""
        count = 0
        for role in queryset.filter(statut='VALIDE'):
            role.statut = 'SUSPENDU'
            role.save()
            count += 1
        
        self.message_user(request, f'{count} rôle(s) suspendu(s).')
    suspendre_roles.short_description = "Suspendre les rôles sélectionnés"