"""
API v3: pagamentos, saldo, saque (stub), idempotência em POST.
"""

import logging

from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from rest_framework import status, views
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import IdempotencyRecord, PaymentIntent, Tenant, Wallet
from .serializers import CreateIntentSerializer, PaymentIntentSerializer
from .services.fx_service import get_fx_service
from .services.fraud_service import evaluate_intent_creation
from .services.ledger_service import ensure_wallet

logger = logging.getLogger(__name__)


def _tenant_from_request(request, data):
    key = (request.headers.get("X-PayPi-Tenant-Key") or "").strip() or (
        (data.get("tenant_api_key") or "").strip() if isinstance(data.get("tenant_api_key"), str) else ""
    )
    if not key:
        return None
    return Tenant.objects.filter(api_key=key).first()


class V3PaymentCreateView(views.APIView):
    """
    POST /api/v3/payments — cria PaymentIntent (checkout) com antifraude e idempotência.
    Header opcional: Idempotency-Key (mesmo corpo → mesma resposta em cache).
    """

    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key="ip", rate="60/m", method="POST"))
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        idem = (request.headers.get("Idempotency-Key") or "").strip()
        if idem:
            cached = IdempotencyRecord.objects.filter(scope="v3:payments", key=idem).first()
            if cached:
                return Response(cached.response_body, status=cached.status_code)

        s = CreateIntentSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data

        tenant = _tenant_from_request(request, data)
        if (request.headers.get("X-PayPi-Tenant-Key") or data.get("tenant_api_key")) and not tenant:
            return Response({"detail": "Invalid tenant API key"}, status=status.HTTP_401_UNAUTHORIZED)

        decision, reason = evaluate_intent_creation(tenant, data["amount_pi"])
        if decision == "blocked":
            return Response(
                {"detail": reason or "blocked", "code": "fraud_blocked"},
                status=status.HTTP_403_FORBIDDEN,
            )
        if decision == "manual_review":
            return Response(
                {"detail": reason or "manual_review", "code": "manual_review"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        fx_service = get_fx_service()
        fx_quote = fx_service.get_quote(data["amount_pi"])
        amount_brl = fx_service.convert(data["amount_pi"]) if fx_quote.get("rate") else None

        intent = PaymentIntent.objects.create(
            intent_id=f"pi_{int(timezone.now().timestamp() * 1000)}",
            payer_address="onchain_tbd",
            payee_user_id=data["payee_user_id"],
            amount_pi=data["amount_pi"],
            amount_brl=amount_brl,
            fx_quote=fx_quote,
            metadata=data.get("metadata", {}),
            tenant=tenant,
            payment_type=data.get("payment_type", PaymentIntent.PAY_ONE_TIME),
        )

        body = dict(PaymentIntentSerializer(intent).data)
        resp = Response(body, status=status.HTTP_201_CREATED)
        if idem:
            IdempotencyRecord.objects.update_or_create(
                scope="v3:payments",
                key=idem,
                defaults={
                    "response_body": body,
                    "status_code": 201,
                },
            )
        logger.info(
            "v3_payment_created",
            extra={"intent_id": intent.intent_id, "tenant_id": getattr(tenant, "id", None)},
        )
        return resp


class V3BalanceView(views.APIView):
    """GET /api/v3/balance — saldos PI/BRL (header X-PayPi-Tenant-Key)."""

    permission_classes = [AllowAny]

    def get(self, request):
        key = (request.headers.get("X-PayPi-Tenant-Key") or "").strip()
        if not key:
            return Response(
                {"detail": "Missing X-PayPi-Tenant-Key header"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        tenant = Tenant.objects.filter(api_key=key).first()
        if not tenant:
            return Response(
                {"detail": "Invalid tenant API key"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        pi = ensure_wallet(tenant, Wallet.ASSET_PI)
        brl = ensure_wallet(tenant, Wallet.ASSET_BRL)
        return Response(
            {
                "tenant_slug": tenant.slug,
                "wallets": [
                    {"asset": pi.asset, "balance": str(pi.balance)},
                    {"asset": brl.asset, "balance": str(brl.balance)},
                ],
            }
        )


class V3WithdrawView(views.APIView):
    """POST /api/v3/withdraw — reservado (saque BRL); ainda não implementado."""

    permission_classes = [AllowAny]

    def post(self, request):
        return Response(
            {"detail": "withdraw_not_implemented", "code": "not_implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
