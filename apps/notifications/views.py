"""
Vues pour le module notifications
Plateforme crowdBuilding - Burkina Faso
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def list_notifications(request):
    """Liste des notifications de l'utilisateur"""
    notifications = request.user.notifications.all()
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_read(request, notification_id):
    """Marquer une notification comme lue"""
    notification = get_object_or_404(Notification, id=notification_id, utilisateur=request.user)
    notification.marquer_comme_lue()
    return JsonResponse({'status': 'success'})
