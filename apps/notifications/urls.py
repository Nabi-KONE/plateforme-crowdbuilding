from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.list_notifications, name='list'),
    # Actions sur les notifications
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('mark-read/<int:notification_id>/', views.mark_read, name='mark_read'),
    path('delete/<int:notification_id>/', views.delete_notification, name='delete'),
    path('delete-all/', views.delete_all_notifications, name='delete_all'),   
]