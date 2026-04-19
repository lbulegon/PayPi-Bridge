"""
Notificações HTTP para o webhook do tenant (best-effort; não falha o fluxo principal).
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import requests

from app.paypibridge.models import PaymentIntent

logger = logging.getLogger(__name__)


def notify_payment_intent_webhook(intent: PaymentIntent, extra: Dict[str, Any] | None = None) -> None:
    if not intent.tenant_id or not (intent.tenant.webhook_url or "").strip():
        return
    url = intent.tenant.webhook_url.strip()
    payload = {
        "event": "payment_intent_updated",
        "intent_id": intent.intent_id,
        "status": intent.status,
        "amount_pi": str(intent.amount_pi),
        "amount_brl": str(intent.amount_brl) if intent.amount_brl is not None else None,
        "settlement_status": intent.settlement_status,
    }
    if extra:
        payload.update(extra)
    try:
        requests.post(url, json=payload, timeout=8)
    except requests.RequestException as exc:
        logger.warning("Tenant webhook failed: %s", exc, extra={"intent_id": intent.intent_id, "url": url})
