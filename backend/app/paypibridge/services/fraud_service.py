"""
Regras antifraude iniciais (valor, volume por tenant).
"""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal
from typing import Literal, Optional, Tuple

from django.conf import settings
from django.utils import timezone

from app.paypibridge.models import PaymentIntent, Tenant

logger = logging.getLogger(__name__)

FraudDecision = Literal["ok", "manual_review", "blocked"]


def _max_pi_single() -> Decimal:
    raw = getattr(settings, "FRAUD_MAX_PI_SINGLE", Decimal("10000"))
    return Decimal(str(raw))


def _max_intents_per_hour() -> int:
    return int(getattr(settings, "FRAUD_MAX_INTENTS_PER_HOUR", 120))


def evaluate_intent_creation(
    tenant: Optional[Tenant],
    amount_pi: Decimal,
) -> Tuple[FraudDecision, Optional[str]]:
    """
    Retorna (decisão, código/motivo).
    Sem tenant: só valida teto global de valor.
    """
    if amount_pi > _max_pi_single():
        logger.warning(
            "fraud_manual_review_amount",
            extra={"amount_pi": str(amount_pi), "tenant_id": getattr(tenant, "id", None)},
        )
        return "manual_review", "amount_above_threshold"

    if tenant:
        since = timezone.now() - timedelta(hours=1)
        n = PaymentIntent.objects.filter(tenant=tenant, created_at__gte=since).count()
        if n >= _max_intents_per_hour():
            logger.warning(
                "fraud_blocked_rate",
                extra={"tenant_id": tenant.id, "count_1h": n},
            )
            return "blocked", "too_many_intents_per_hour"

    return "ok", None
