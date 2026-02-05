from django.utils import timezone
from django.shortcuts import render

# Create your views here.
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from apps.investments.models import (
    Investissement,
    Transaction,
    StatutInvestissement,
    StatutTransaction,
    TypeTransaction
)

# ======================================================
# 1️⃣ INITIATION DU PAIEMENT (remplace simuler_paiement)
# ======================================================
@login_required
def init_mock_payment(request, investment_id):

    investissement = get_object_or_404(
        Investissement,
        id=investment_id,
        investisseur=request.user,
        statut=StatutInvestissement.EN_ATTENTE_PAIEMENT
    )

    transaction = investissement.transactions.filter(
        statut=StatutTransaction.EN_ATTENTE
    ).last()

    if not transaction:
        return JsonResponse({
            "success": False,
            "message": "Aucune transaction en attente."
        }, status=400)

    # Redirection vers la page de paiement simulée
    return redirect(
        'payments:mock_pay',
        transaction_id=transaction.id
    )

# ======================================================
# 2️⃣ PAGE DE PAIEMENT SIMULÉE
# ======================================================
@login_required
def mock_pay(request, transaction_id):

    transaction = get_object_or_404(Transaction, id=transaction_id)

    if request.method == 'POST':
        resultat = request.POST.get('resultat')  # SUCCESS / FAILED

        payload = {
            "reference": transaction.reference,
            "status": resultat
        }

        return redirect(
            'payments:webhook'
        )

    return render(request, 'payments/mock_pay.html', {
        'transaction': transaction
    })

# ======================================================
# 3️⃣ WEBHOOK (SOURCE UNIQUE DE VÉRITÉ)
# ======================================================
@csrf_exempt
@require_POST
def payment_webhook(request):

    data = json.loads(request.body)

    transaction = get_object_or_404(
        Transaction,
        reference=data['reference']
    )

    if data['status'] == 'SUCCESS':
        transaction.valider_paiement()
    else:
        transaction.statut = StatutTransaction.ECHOUEE
        transaction.save()

    return JsonResponse({"success": True})

# ======================================================
# 4️⃣ MOCK API PAYMENT (POST JSON)
# ======================================================
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from apps.investments.models import Investissement, Transaction, StatutTransaction, StatutInvestissement

@login_required
def mock_api_payment(request, investment_id):
    """
    Simulation d'une API de paiement pour un investissement.
    Met à jour le statut de l'investissement et crée une transaction fictive.
    """
    investissement = get_object_or_404(Investissement, id=investment_id)

    if request.method == "GET":
        # 🔹 Vérifier que l'investissement n'est pas déjà payé
        if investissement.statut == StatutInvestissement.CONFIRME.value:
            return JsonResponse({"success": False, "message": "Investissement déjà validé."})

        # 🔹 Définir un statut existant sûr
        # Si tu veux un statut spécial "en attente validation admin", il faut l'ajouter à l'Enum
        # Sinon, utiliser EN_ATTENTE qui existe déjà
        investissement.statut = StatutInvestissement.EN_ATTENTE_PAIEMENT.value
        investissement.date_investissement = timezone.now()
        investissement.save()

        # 🔹 Créer une transaction fictive (pour simuler le paiement)
        Transaction.objects.create(
            investissement=investissement,
            montant=investissement.montant,
            type=TypeTransaction.INVESTISSEMENT,
            statut=StatutTransaction.EN_ATTENTE,
            mode_paiement="MOCK",
            description=f"Paiement simulé pour l'investissement {investissement.id}"
        )

        return JsonResponse({
            "success": True,
            "message": "Paiement simulé avec succès.",
            "investissement_id": investissement.id
        })

    return JsonResponse({"success": False, "message": "Méthode non autorisée."})
