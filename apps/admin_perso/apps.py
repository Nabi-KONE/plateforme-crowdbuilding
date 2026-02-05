from django.apps import AppConfig

class AdminPersoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.admin_perso'  # ⚡ Doit correspondre au chemin exact du dossier
    verbose_name = "Administration Personnalisée"
