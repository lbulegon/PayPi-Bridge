import os, hmac, hashlib
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.utils import timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from .models import PaymentIntent, PixTransaction, Consent, BankAccount
from .serializers import (
    CreateIntentSerializer, PaymentIntentSerializer,
    PixPayoutSerializer, VerifyPaymentSerializer,
    CreateConsentSerializer, ConsentSerializer,
    LinkBankAccountSerializer, ReconcilePaymentSerializer
)
from .clients.pix import PixClient
from .services.pi_service import get_pi_service
from .services.consent_service import get_consent_service


def _verify_hmac(body: bytes, signature: str, secret: str) -> bool:
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)


def _get_user_for_request(request, user_id_from_data=None):
    """Usuário efetivo: autenticado ou user_id (default 1). Autenticação será implementada depois."""
    if request.user and getattr(request.user, "is_authenticated", True) and request.user.is_authenticated:
        return request.user
    uid = user_id_from_data if user_id_from_data is not None else 1
    return get_user_model().objects.filter(id=uid).first()


class IntentView(views.APIView):
    """
    Create a PaymentIntent for Pi → BRL conversion.
    This creates a local intent that will be tied to an on-chain Soroban contract.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = CreateIntentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        
        # Create PaymentIntent
        intent = PaymentIntent.objects.create(
            intent_id=f"pi_{int(timezone.now().timestamp() * 1000)}",
            payer_address="onchain_tbd",  # Will be updated when Pi payment is received
            payee_user_id=data["payee_user_id"],
            amount_pi=data["amount_pi"],
            metadata=data.get("metadata", {}),
        )
        
        return Response(PaymentIntentSerializer(intent).data, status=status.HTTP_201_CREATED)


class IntentListView(views.APIView):
    """
    List PaymentIntents (for testing). Returns minimal list: id, intent_id, status, amount_pi, created_at.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        intents = PaymentIntent.objects.all().order_by("-created_at")[:50]
        data = [
            {
                "id": i.id,
                "intent_id": i.intent_id,
                "status": i.status,
                "amount_pi": str(i.amount_pi),
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in intents
        ]
        return Response(data)


class VerifyPiPaymentView(views.APIView):
    """
    Verify a Pi Network payment and link it to a PaymentIntent.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = VerifyPaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        
        payment_id = data.get("payment_id")
        intent_id = data.get("intent_id")
        
        # Get Pi service
        pi_service = get_pi_service()
        if not pi_service.is_available():
            return Response(
                {"detail": "Pi Network integration not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Verify payment with Pi Network
        payment = pi_service.verify_payment(payment_id)
        if not payment:
            return Response(
                {"detail": "Payment not found or invalid"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check payment status
        payment_status = payment.get("status", {})
        if payment_status.get("cancelled") or payment_status.get("user_cancelled"):
            return Response(
                {"detail": "Payment was cancelled"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not payment_status.get("transaction_verified"):
            return Response(
                {"detail": "Payment transaction not yet verified"},
                status=status.HTTP_202_ACCEPTED
            )
        
        # Update PaymentIntent with Pi payment info
        try:
            intent = PaymentIntent.objects.get(intent_id=intent_id)
            intent.payer_address = payment.get("from_address", "")
            intent.metadata = {
                **intent.metadata,
                "pi_payment_id": payment_id,
                "pi_txid": payment.get("transaction", {}).get("txid", ""),
                "pi_verified": True
            }
            intent.save()
            
            return Response({
                "intent_id": intent.intent_id,
                "payment_id": payment_id,
                "verified": True,
                "txid": payment.get("transaction", {}).get("txid", "")
            })
        except PaymentIntent.DoesNotExist:
            return Response(
                {"detail": "PaymentIntent not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class CCIPWebhookView(views.APIView):
    """
    Webhook endpoint for CCIP/Relayer events.
    Valida HMAC (X-Signature), atualiza PaymentIntent (fx_quote, amount_brl, status).
    Idempotência: se payload tiver event_id, mesmo evento não processa duas vezes.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        secret = os.getenv("CCIP_WEBHOOK_SECRET", "")
        sig = request.headers.get("X-Signature", "")
        if not secret:
            return Response(
                {"detail": "CCIP_WEBHOOK_SECRET not configured"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        if not _verify_hmac(request.body, sig, secret):
            return Response(
                {"detail": "invalid signature"},
                status=status.HTTP_403_FORBIDDEN
            )

        payload = request.data
        intent_id = payload.get("intent_id")
        if not intent_id:
            return Response(
                {"detail": "intent_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        event_id = payload.get("event_id")
        if event_id:
            if WebhookEvent.objects.filter(intent_id=intent_id, event_id=event_id).exists():
                return Response({"ok": True, "already_processed": True})

        try:
            intent = PaymentIntent.objects.get(intent_id=intent_id)
        except PaymentIntent.DoesNotExist:
            return Response(
                {"detail": "intent not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        fx_quote = payload.get("fx_quote") or {}
        intent.fx_quote = fx_quote
        brl_amount = fx_quote.get("brl_amount")
        if brl_amount is not None:
            try:
                intent.amount_brl = Decimal(str(brl_amount))
            except (ValueError, TypeError):
                pass
        new_status = payload.get("status") or "CONFIRMED"
        if new_status in dict(PaymentIntent.STATUS):
            intent.status = new_status
        intent.save(update_fields=["fx_quote", "amount_brl", "status"])

        if event_id:
            WebhookEvent.objects.get_or_create(intent_id=intent_id, event_id=event_id)

        return Response({"ok": True})


class PixPayoutView(views.APIView):
    """
    Create a Pix payout using Open Finance.
    This converts the confirmed PaymentIntent into a real Pix transaction.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = PixPayoutSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        consent = Consent.objects.filter(
            user_id=data["payee_user_id"],
            status="ACTIVE"
        ).first()
        
        if not consent:
            return Response(
                {"detail": "no active consent"},
                status=status.HTTP_400_BAD_REQUEST
            )

        pix = PixClient.from_env(consent=consent)
        
        try:
            tx = pix.create_immediate_payment(
                cpf=data["cpf"],
                pix_key=data["pix_key"],
                amount_brl=str(data["amount_brl"]),
                description=data.get("description", "")
            )
        except ValueError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        intent = PaymentIntent.objects.filter(
            payee_user_id=data["payee_user_id"]
        ).order_by("-id").first()
        
        if intent:
            p = PixTransaction.objects.create(
                intent=intent,
                tx_id=tx["txid"],
                status=tx["status"],
                payload=tx
            )
            
            # Update intent status to SETTLED
            intent.status = "SETTLED"
            intent.save(update_fields=["status"])
            
            return Response({
                "txid": p.tx_id,
                "status": p.status,
                "intent_id": intent.intent_id
            })
        
        return Response({
            "txid": tx["txid"],
            "status": tx["status"]
        })


class PiStatusView(views.APIView):
    """
    Status da integração Pi Network (configurado ou não, sem expor credenciais).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        pi_service = get_pi_service()
        configured = pi_service.is_available()
        return Response({
            "configured": configured,
            "network": pi_service.network,
            "message": "Pi Network configurado. Use GET /api/pi/balance para saldo."
            if configured
            else "Configure PI_API_KEY e PI_WALLET_PRIVATE_SEED no .env e reinicie o backend.",
        })


class PiBalanceView(views.APIView):
    """
    Get the current Pi balance of the app wallet.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        pi_service = get_pi_service()
        if not pi_service.is_available():
            return Response(
                {"detail": "Pi Network integration not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        balance = pi_service.get_balance()
        if balance is None:
            return Response(
                {"detail": "Unable to retrieve balance"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response({
            "balance": str(balance),
            "network": pi_service.network
        })


class ConsentView(views.APIView):
    """
    Create a new Open Finance consent (POST) or list user's consents (GET).
    Sem autenticação: use user_id no body (POST) ou query (GET), default 1.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = CreateConsentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        user = _get_user_for_request(request, data.get("user_id"))
        if not user:
            return Response(
                {"detail": "Usuário não encontrado. Use user_id válido ou crie com createtestuser."},
                status=status.HTTP_400_BAD_REQUEST
            )
        consent_service = get_consent_service()
        consent = consent_service.create_consent(
            user=user,
            provider=data["provider"],
            scopes=data["scopes"],
            expiration_days=data.get("expiration_days", 90)
        )
        if not consent:
            return Response(
                {"detail": "Failed to create consent"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response(ConsentSerializer(consent).data, status=status.HTTP_201_CREATED)

    def get(self, request):
        """List user's consents. Query: user_id (default 1)."""
        user_id = request.query_params.get("user_id", 1)
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            user_id = 1
        user = get_user_model().objects.filter(id=user_id).first()
        if not user:
            return Response({"detail": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        consents = Consent.objects.filter(user=user)
        return Response(ConsentSerializer(consents, many=True).data)


class ConsentDetailView(views.APIView):
    """
    Get (GET) or refresh (POST) a specific consent.
    Query: user_id (default 1). Autenticação será implementada depois.
    """
    permission_classes = [AllowAny]

    def _get_consent(self, request, consent_id):
        user_id = request.query_params.get("user_id", request.data.get("user_id", 1))
        try:
            user_id = int(user_id)
        except (TypeError, ValueError):
            user_id = 1
        return Consent.objects.filter(id=consent_id, user_id=user_id).first()

    def get(self, request, consent_id):
        consent = self._get_consent(request, consent_id)
        if not consent:
            return Response(
                {"detail": "Consent not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(ConsentSerializer(consent).data)

    def post(self, request, consent_id):
        """Refresh consent data from Open Finance."""
        consent = self._get_consent(request, consent_id)
        if not consent:
            return Response(
                {"detail": "Consent not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        consent_service = get_consent_service()
        if consent_service.refresh_consent(consent):
            return Response(ConsentSerializer(consent).data)
        return Response(
            {"detail": "Failed to refresh consent"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class LinkBankAccountView(views.APIView):
    """
    Link a bank account to a consent. Body: user_id (default 1). Autenticação depois.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = LinkBankAccountSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        user_id = data.get("user_id", 1)
        consent = Consent.objects.filter(id=data["consent_id"], user_id=user_id).first()
        if not consent:
            return Response(
                {"detail": "Consent not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        consent_service = get_consent_service()
        
        bank_account = consent_service.link_bank_account(
            consent=consent,
            institution=data["institution"],
            account_id=data["account_id"],
            branch=data.get("branch", ""),
            number=data.get("number", ""),
            ispb=data.get("ispb", "")
        )
        
        if not bank_account:
            return Response(
                {"detail": "Failed to link bank account"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        from .serializers import BankAccountSerializer
        return Response(BankAccountSerializer(bank_account).data, status=status.HTTP_201_CREATED)


class ReconcilePaymentView(views.APIView):
    """
    Reconcile a payment by checking account transactions. Body: user_id (default 1).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = ReconcilePaymentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        user_id = data.get("user_id", 1)
        consent = Consent.objects.filter(id=data["consent_id"], user_id=user_id).first()
        if not consent:
            return Response(
                {"detail": "Consent not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        from .clients.open_finance import OpenFinanceClient
        of_client = OpenFinanceClient.from_env()
        
        result = of_client.reconcile_payment(
            consent_id=consent.consent_id,
            account_id=data["account_id"],
            expected_amount=str(data["expected_amount"]),
            expected_txid=data.get("expected_txid")
        )
        
        if not result:
            return Response(
                {"detail": "Payment not found in transactions"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(result)
