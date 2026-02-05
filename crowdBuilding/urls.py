"""
URL configuration for crowdBuilding project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin Django (classique) - namespace implicite 'admin'
    path('admin/', admin.site.urls),
    
    # Votre admin personnalisé - namespace différent
    path('admin-perso/', include('apps.admin_perso.urls', namespace='admin_perso')),  # ⚡ chemin complet
    # Vos autres URLs
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('projects/', include('apps.projects.urls')),
    path('investments/', include('apps.investments.urls')),
    path('documents/', include('apps.documents.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('payments/', include('apps.payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Servir les fichiers média en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configuration de l'admin
admin.site.site_header = "crowdBuilding - Administration"
admin.site.site_title = "crowdBuilding Admin"
admin.site.index_title = "Plateforme de Financement Participatif Immobilier"
