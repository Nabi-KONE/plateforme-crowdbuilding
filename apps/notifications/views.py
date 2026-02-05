"""
Vues pour le module notifications
Plateforme crowdBuilding - Burkina Faso
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Notification, ParametreNotification, TypeNotification
from django.views.decorators.http import require_http_methods
from .forms import ParametreNotificationForm
from django.core.paginator import Paginator
from django.db.models import Q, Count  # 🔥 CORRECTION : Ajout de Q
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from apps.investments.models import Investissement, StatutInvestissement



@login_required
def list_notifications(request):
    """Liste des notifications de l'utilisateur connecté"""

    notifications = request.user.notifications.all().order_by('-date_creation')

    # Filtres
    filter_param = request.GET.get('filter', 'toutes')
    if filter_param == 'non_lues':
        notifications = notifications.filter(lue=False)
    elif filter_param == 'projets':
        notifications = notifications.filter(projet__isnull=False)
    elif filter_param == 'investissements':
        notifications = notifications.filter(investissement__isnull=False)

    context = {
        'notifications': notifications,
        'total_count': notifications.count(),
        'unread_count': notifications.filter(lue=False).count(),
    }

    # === PROMOTEUR ===
    if request.user.est_promoteur():
        parametres, _ = ParametreNotification.objects.get_or_create(
            utilisateur=request.user
        )
        form = ParametreNotificationForm(instance=parametres)

        if request.method == 'POST':
            form = ParametreNotificationForm(request.POST, instance=parametres)
            if form.is_valid():
                form.save()
                messages.success(request, "Paramètres mis à jour.")
                return redirect('notifications:list')

        context['form'] = form
        return render(request, 'promoteur/notifications.html', context)

    # === INVESTISSEUR ===
    if request.user.est_investisseur():

        # ✅ CAPITAL CONFIRMÉ (argent réellement validé)
        total_confirme = Investissement.objects.filter(
            investisseur=request.user,
            statut=StatutInvestissement.CONFIRME
        ).aggregate(total=Sum('montant'))['total'] or 0

        # ✅ NOMBRE DE PROJETS INVESTIS
        nb_projets_investis = Investissement.objects.filter(
            investisseur=request.user,
            statut=StatutInvestissement.CONFIRME
        ).values('projet').distinct().count()

        # 🔁 Injection dans le contexte
        context.update({
            'total_confirme': total_confirme,
            'nb_projets_investis': nb_projets_investis,
        })

        return render(request, 'notifications/list_investisseur.html', context)


    # === ADMIN ===
    if request.user.est_administrateur():
        return render(request, 'notifications/list_admin.html', context)

    return render(request, 'notifications/list_pending.html', context)


@require_POST
@login_required
def mark_all_read(request):
    """Marquer toutes les notifications comme lues"""
    try:
        if request.user.est_administrateur():
            # Admin: marquer toutes les notifications
            updated_count = Notification.objects.filter(lue=False).update(lue=True)
        else:
            # Utilisateur normal: seulement ses notifications
            updated_count = request.user.notifications.filter(lue=False).update(lue=True)
            
        return JsonResponse({
            'success': True,
            'message': f'{updated_count} notification(s) marquée(s) comme lue(s)',
            'updated_count': updated_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })
    
@require_POST
@login_required
def mark_read(request, notification_id):
    """Marquer une notification comme lue"""
    try:
        if request.user.est_administrateur():
            # Admin peut marquer n'importe quelle notification
            notification = Notification.objects.get(id=notification_id)
        else:
            # Utilisateur normal: seulement ses notifications
            notification = Notification.objects.get(id=notification_id, utilisateur=request.user)
            
        notification.marquer_comme_lue()
        return JsonResponse({
            'success': True,
            'message': 'Notification marquée comme lue'
        })
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Notification non trouvée'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })


@require_POST
@login_required
def delete_notification(request, notification_id):
    """Supprimer une notification"""
    try:
        if request.user.est_administrateur():
            # Admin peut supprimer n'importe quelle notification
            notification = Notification.objects.get(id=notification_id)
        else:
            # Utilisateur normal: seulement ses notifications
            notification = Notification.objects.get(id=notification_id, utilisateur=request.user)
            
        notification.delete()
        return JsonResponse({
            'success': True,
            'message': 'Notification supprimée'
        })
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Notification non trouvée'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })

@require_POST
@login_required
def delete_all_notifications(request):
    """Supprimer toutes les notifications"""
    try:
        if request.user.est_administrateur():
            # Admin peut supprimer toutes les notifications
            deleted_count = Notification.objects.count()
            Notification.objects.all().delete()
        else:
            # Utilisateur normal: seulement ses notifications
            deleted_count = request.user.notifications.count()
            request.user.notifications.all().delete()
            
        return JsonResponse({
            'success': True,
            'message': f'{deleted_count} notification(s) supprimée(s)',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur: {str(e)}'
        })