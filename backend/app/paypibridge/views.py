import os, hmac, hashlib
from rest_framework import status, views
from rest_framework.response import Response
from django.utils import timezone

from .models import PaymentIntent, PixTransaction, Consent
from .serializers import (
    CreateIntentSerializer, PaymentIntentSerializer,
    PixPayoutSerializer
)
from .clients.pix import PixClient

def _verify_hmac(body: bytes, signature: str, secret: str) -> bool:
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)

class IntentView(views.APIView):
    def post(self, request):
        s = CreateIntentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        intent = PaymentIntent.objects.create(
            intent_id=f"pi_{timezone.now().timestamp()}",
            payer_address="onchain_tbd",
            payee_user_id=data["payee_user_id"],
            amount_pi=data["amount_pi"],
            metadata=data.get("metadata", {}),
        )
        return Response(PaymentIntentSerializer(intent).data, status=201)

class CCIPWebhookView(views.APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        secret = os.getenv("CCIP_WEBHOOK_SECRET","")
        sig = request.headers.get("X-Signature","")
        if not _verify_hmac(request.body, sig, secret):
            return Response({"detail":"invalid signature"}, status=403)

        payload = request.data  # {intent_id, fx_quote:{brl_amount}, payee_user_id,...}
        try:
            intent = PaymentIntent.objects.get(intent_id=payload["intent_id"])
        except PaymentIntent.DoesNotExist:
            return Response({"detail":"intent not found"}, status=404)

        intent.fx_quote = payload.get("fx_quote", {})
        intent.amount_brl = payload.get("fx_quote", {}).get("brl_amount")
        intent.status = "CONFIRMED"
        intent.save(update_fields=["fx_quote","amount_brl","status"])
        return Response({"ok":True})

class PixPayoutView(views.APIView):
    def post(self, request):
        s = PixPayoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        consent = Consent.objects.filter(user_id=data["payee_user_id"], status="ACTIVE").first()
        if not consent:
            return Response({"detail":"no active consent"}, status=400)

        pix = PixClient.from_env(consent=consent)
        tx = pix.create_immediate_payment(
            cpf=data["cpf"],
            pix_key=data["pix_key"],
            amount_brl=str(data["amount_brl"]),
            description=data.get("description","")
        )
        intent = PaymentIntent.objects.filter(payee_user_id=data["payee_user_id"]).order_by("-id").first()
        p = PixTransaction.objects.create(intent=intent, tx_id=tx["txid"], status=tx["status"], payload=tx)
        return Response({"txid": p.tx_id, "status": p.status})
