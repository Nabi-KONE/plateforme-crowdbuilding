from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('init/<int:investment_id>/', views.init_mock_payment, name='init'),
    path('pay/<int:transaction_id>/', views.mock_pay, name='mock_pay'),
    path('webhook/', views.payment_webhook, name='webhook'),
    path('mock-api/<int:investment_id>/', views.mock_api_payment, name='mock_api_payment'),
]

