import os
import hmac
import hashlib
import logging
from rest_framework import status, views
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils import timezone
from decimal import Decimal
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

from django.contrib.auth import get_user_model
from .models import PaymentIntent, PixTransaction, Consent, BankAccount, WebhookEvent

logger = logging.getLogger(__name__)
from .serializers import (
    CreateIntentSerializer, PaymentIntentSerializer,
    PixPayoutSerializer, VerifyPaymentSerializer,
    CreateConsentSerializer, ConsentSerializer,
    LinkBankAccountSerializer, ReconcilePaymentSerializer
)
from .clients.pix import PixClient
from .services.pi_service import get_pi_service
from .services.consent_service import get_consent_service
from .services.fx_service import get_fx_service
from .services.relayer import get_relayer
from .permissions import IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly


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
    Rate limited to prevent abuse.
    """
    permission_classes = [AllowAny]  # Keep AllowAny for public checkout, but rate limit
    
    @method_decorator(ratelimit(key='ip', rate='30/m', method='POST'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        s = CreateIntentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        
        # Get FX quote for amount
        fx_service = get_fx_service()
        fx_quote = fx_service.get_quote(data["amount_pi"])
        amount_brl = fx_service.convert(data["amount_pi"]) if fx_quote.get('rate') else None
        
        # Create PaymentIntent
        intent = PaymentIntent.objects.create(
            intent_id=f"pi_{int(timezone.now().timestamp() * 1000)}",
            payer_address="onchain_tbd",  # Will be updated when Pi payment is received
            payee_user_id=data["payee_user_id"],
            amount_pi=data["amount_pi"],
            amount_brl=amount_brl,
            fx_quote=fx_quote,
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
                {"detail": "Could not retrieve balance"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response({
            "balance": str(balance),
            "network": pi_service.network
        })


class FXQuoteView(views.APIView):
    """
    Get FX quote for Pi → BRL conversion.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get current FX rate."""
        fx_service = get_fx_service()
        rate = fx_service.get_rate()
        
        if rate is None:
            return Response(
                {"detail": "FX rate unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response({
            "from_currency": "PI",
            "to_currency": "BRL",
            "rate": str(rate),
            "provider": fx_service.provider,
            "cache_ttl": fx_service.cache_timeout
        })
    
    def post(self, request):
        """Get FX quote for specific amount."""
        amount_pi_str = request.data.get('amount_pi')
        if not amount_pi_str:
            return Response(
                {"detail": "amount_pi is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            amount_pi = Decimal(str(amount_pi_str))
        except (ValueError, TypeError):
            return Response(
                {"detail": "Invalid amount_pi format"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fx_service = get_fx_service()
        quote = fx_service.get_quote(amount_pi)
        
        return Response(quote)

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
    Manage Open Finance consents.
    Requires authentication.
    """
    permission_classes = [IsAuthenticated]
    
    @method_decorator(ratelimit(key='ip', rate='20/m', method='POST'))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

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


class RelayerStatusView(views.APIView):
    """
    Get status of Soroban Relayer service.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get relayer status and configuration."""
        relayer = get_relayer()
        status = relayer.get_status()
        return Response(status)
    
    def post(self, request):
        """Manually trigger event monitoring (for testing)."""
        relayer = get_relayer()
        events = relayer.monitor_contract_events(relayer._last_ledger)
        
        processed = 0
        for event in events:
            if relayer.process_event(event):
                processed += 1
        
        return Response({
            "events_found": len(events),
            "processed": processed,
            "status": relayer.get_status()
        })


class PiNetworkWebhookView(views.APIView):
    """
    Webhook endpoint for Pi Network payment events.
    Receives events from Pi Network about payment status changes.
    """
    authentication_classes = []
    permission_classes = []
    
    def post(self, request):
        """
        Process Pi Network webhook event.
        
        Expected events:
        - payment_created: New payment created
        - payment_completed: Payment completed
        - payment_cancelled: Payment cancelled
        - payment_failed: Payment failed
        """
        # Pi Network webhook validation (if they provide signature)
        pi_webhook_secret = os.getenv('PI_WEBHOOK_SECRET', '')
        if pi_webhook_secret:
            signature = request.headers.get('X-Pi-Signature', '')
            if signature and not _verify_hmac(request.body, signature, pi_webhook_secret):
                return Response(
                    {"detail": "invalid signature"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        payload = request.data
        event_type = payload.get('type') or payload.get('event_type')
        payment_id = payload.get('payment_id') or payload.get('identifier')
        
        if not payment_id:
            return Response(
                {"detail": "payment_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process event asynchronously
        from .tasks import process_pi_webhook_event
        process_pi_webhook_event.delay(payload)
        
        logger.info(
            f"Pi Network webhook received",
            extra={
                'event_type': event_type,
                'payment_id': payment_id,
                'request_id': getattr(request, 'request_id', None)
            }
        )
        
        return Response({"ok": True, "received": True})


class HealthCheckView(views.APIView):
    """
    Comprehensive health check endpoint.
    Checks all integrations and services.
    """
    authentication_classes = []
    permission_classes = []
    
    def get(self, request):
        """Get health status of all services."""
        health = {
            "status": "healthy",
            "timestamp": timezone.now().isoformat(),
            "services": {}
        }
        
        # Check Pi Network
        pi_service = get_pi_service()
        pi_available = pi_service.is_available()
        health["services"]["pi_network"] = {
            "available": pi_available,
            "configured": bool(os.getenv('PI_API_KEY') and os.getenv('PI_WALLET_PRIVATE_SEED'))
        }
        if not pi_available:
            health["status"] = "degraded"
        
        # Check Open Finance
        try:
            from .clients.open_finance import OpenFinanceClient
            of_client = OpenFinanceClient.from_env()
            health["services"]["open_finance"] = {
                "configured": bool(
                    os.getenv('OPEN_FINANCE_CLIENT_ID') and
                    os.getenv('OPEN_FINANCE_CLIENT_SECRET')
                ),
                "available": True  # Could add actual connectivity check
            }
        except Exception as e:
            health["services"]["open_finance"] = {
                "configured": False,
                "available": False,
                "error": str(e)
            }
            health["status"] = "degraded"
        
        # Check Soroban Relayer
        relayer = get_relayer()
        relayer_status = relayer.get_status()
        health["services"]["soroban_relayer"] = {
            "enabled": relayer_status.get("enabled", False),
            "connected": relayer_status.get("connected", False),
            "contract_id": relayer_status.get("contract_id", "not_configured")
        }
        if not relayer_status.get("enabled"):
            health["status"] = "degraded"
        
        # Check FX Service
        try:
            fx_service = get_fx_service()
            health["services"]["fx_service"] = {
                "available": True,
                "provider": os.getenv('FX_PROVIDER', 'fixed')
            }
        except Exception as e:
            health["services"]["fx_service"] = {
                "available": False,
                "error": str(e)
            }
            health["status"] = "degraded"
        
        # Check Database
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health["services"]["database"] = {"available": True}
        except Exception as e:
            health["services"]["database"] = {
                "available": False,
                "error": str(e)
            }
            health["status"] = "unhealthy"
        
        # Check Redis/Celery
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            cache.get('health_check')
            health["services"]["cache"] = {"available": True}
        except Exception as e:
            health["services"]["cache"] = {
                "available": False,
                "error": str(e)
            }
            health["status"] = "degraded"
        
        # Check Celery
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            health["services"]["celery"] = {
                "available": bool(stats),
                "workers": len(stats) if stats else 0
            }
        except Exception as e:
            health["services"]["celery"] = {
                "available": False,
                "error": str(e)
            }
            health["status"] = "degraded"
        
        status_code = status.HTTP_200_OK
        if health["status"] == "unhealthy":
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif health["status"] == "degraded":
            status_code = status.HTTP_200_OK  # Still OK but degraded
        
        return Response(health, status=status_code)


class TestEndpointsView(views.APIView):
    """
    Test endpoints for validating integrations.
    Useful for debugging and testing configurations.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Get list of available test endpoints."""
        return Response({
            "endpoints": {
                "pi_balance": "/api/test/pi-balance",
                "pi_status": "/api/test/pi-status",
                "fx_rate": "/api/test/fx-rate?amount_pi=10",
                "relayer_status": "/api/test/relayer-status",
                "open_finance_config": "/api/test/open-finance-config"
            }
        })
    
    def post(self, request):
        """Run specific test."""
        test_type = request.data.get('test')
        
        if test_type == 'pi_balance':
            pi_service = get_pi_service()
            balance = pi_service.get_balance()
            return Response({
                "test": "pi_balance",
                "available": pi_service.is_available(),
                "balance": str(balance) if balance else None
            })
        
        elif test_type == 'fx_rate':
            amount_pi = Decimal(str(request.data.get('amount_pi', '10')))
            fx_service = get_fx_service()
            quote = fx_service.get_quote(amount_pi)
            return Response({
                "test": "fx_rate",
                "amount_pi": str(amount_pi),
                "quote": quote
            })
        
        elif test_type == 'relayer':
            relayer = get_relayer()
            status = relayer.get_status()
            # Try to query events
            events = relayer.monitor_contract_events()
            return Response({
                "test": "relayer",
                "status": status,
                "events_found": len(events)
            })
        
        elif test_type == 'open_finance':
            try:
                from .clients.open_finance import OpenFinanceClient
                client = OpenFinanceClient.from_env()
                return Response({
                    "test": "open_finance",
                    "configured": bool(
                        os.getenv('OPEN_FINANCE_CLIENT_ID') and
                        os.getenv('OPEN_FINANCE_CLIENT_SECRET')
                    ),
                    "client_id": os.getenv('OPEN_FINANCE_CLIENT_ID', 'not_set')[:10] + '...' if os.getenv('OPEN_FINANCE_CLIENT_ID') else None
                })
            except Exception as e:
                return Response({
                    "test": "open_finance",
                    "error": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            {"detail": f"Unknown test type: {test_type}"},
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminStatsView(views.APIView):
    """
    Administrative endpoint for monitoring system statistics.
    Requires authentication (can be configured).
    """
    permission_classes = [AllowAny]  # Change to IsAuthenticated in production
    
    def get(self, request):
        """Get system statistics."""
        from django.db.models import Count, Sum, Q
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        stats = {
            "timestamp": now.isoformat(),
            "payment_intents": {
                "total": PaymentIntent.objects.count(),
                "last_24h": PaymentIntent.objects.filter(created_at__gte=last_24h).count(),
                "last_7d": PaymentIntent.objects.filter(created_at__gte=last_7d).count(),
                "by_status": dict(
                    PaymentIntent.objects.values('status')
                    .annotate(count=Count('id'))
                    .values_list('status', 'count')
                ),
                "total_amount_pi": str(
                    PaymentIntent.objects.aggregate(Sum('amount_pi'))['amount_pi__sum'] or 0
                ),
                "total_amount_brl": str(
                    PaymentIntent.objects.aggregate(Sum('amount_brl'))['amount_brl__sum'] or 0
                )
            },
            "pix_transactions": {
                "total": PixTransaction.objects.count(),
                "last_24h": PixTransaction.objects.filter(created_at__gte=last_24h).count(),
                "by_status": dict(
                    PixTransaction.objects.values('status')
                    .annotate(count=Count('id'))
                    .values_list('status', 'count')
                )
            },
            "consents": {
                "total": Consent.objects.count(),
                "active": Consent.objects.filter(status='ACTIVE').count(),
                "expired": Consent.objects.filter(
                    expires_at__lt=now,
                    status='ACTIVE'
                ).count()
            },
            "webhook_events": {
                "total": WebhookEvent.objects.count(),
                "last_24h": WebhookEvent.objects.filter(created_at__gte=last_24h).count()
            },
            "services": {
                "pi_network": {
                    "available": get_pi_service().is_available(),
                    "configured": bool(os.getenv('PI_API_KEY'))
                },
                "soroban_relayer": get_relayer().get_status(),
                "fx_service": {
                    "provider": os.getenv('FX_PROVIDER', 'fixed'),
                    "available": True
                }
            }
        }
        
        return Response(stats)


class AdminIntentsView(views.APIView):
    """
    Administrative endpoint to list and filter PaymentIntents.
    """
    permission_classes = [AllowAny]  # Change to IsAuthenticated in production
    
    def get(self, request):
        """List PaymentIntents with filtering."""
        status_filter = request.query_params.get('status')
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        queryset = PaymentIntent.objects.all().order_by('-created_at')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        intents = queryset[offset:offset + limit]
        
        serializer = PaymentIntentSerializer(intents, many=True)
        
        return Response({
            "count": queryset.count(),
            "results": serializer.data,
            "limit": limit,
            "offset": offset
        })
