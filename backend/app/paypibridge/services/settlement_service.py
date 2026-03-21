"""
Motor de liquidação: Pi (montante) → BRL (câmbio + taxa) → Pix para chave do beneficiário.
Só deve correr após pagamento Pi validado (ex.: verified_at preenchido).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from django.utils import timezone

from app.paypibridge.models import Consent, PaymentIntent, PixTransaction

from .pricing_service import get_pricing_service
from .settlement_pix_port import SettlementPixPort

logger = logging.getLogger(__name__)

# Taxa de serviço sobre o bruto em BRL (0.05 = 5%). Default 0 para não surpreender em prod.
_SETTLEMENT_FEE_RATE = Decimal(os.getenv("SETTLEMENT_FEE_RATE", "0"))


@dataclass
class SettlementResult:
    success: bool
    gross_brl: Optional[Decimal]
    net_brl: Optional[Decimal]
    fee_brl: Optional[Decimal]
    pix_txid: Optional[str]
    error: Optional[str] = None


class SettlementService:
    def __init__(self, pricing_service=None, pix_port: Optional[SettlementPixPort] = None):
        self.pricing = pricing_service or get_pricing_service()
        self.pix_port = pix_port or SettlementPixPort()

    def settle(
        self,
        intent: PaymentIntent,
        *,
        consent: Consent,
        cpf: str,
        pix_key: str,
        description: str = "",
    ) -> SettlementResult:
        if intent.payee_user_id != consent.user_id:
            return SettlementResult(
                False, None, None, None, None, "consent_user_mismatch"
            )

        if not intent.verified_at:
            return SettlementResult(
                False, None, None, None, None, "pi_payment_not_verified"
            )

        if intent.status == "SETTLED":
            return SettlementResult(
                False, None, None, None, None, "already_settled"
            )

        if intent.status == "CANCELLED":
            return SettlementResult(False, None, None, None, None, "intent_cancelled")

        gross = self.pricing.convert_pi_to_brl(intent.amount_pi)
        if gross is None:
            return SettlementResult(
                False, None, None, None, None, "fx_unavailable"
            )

        fee = (gross * _SETTLEMENT_FEE_RATE).quantize(Decimal("0.01"))
        net = (gross - fee).quantize(Decimal("0.01"))
        if net <= 0:
            return SettlementResult(
                False, gross, None, fee, None, "net_amount_non_positive"
            )

        pix_out = self.pix_port.send(
            consent=consent,
            cpf=cpf,
            pix_key=pix_key,
            amount_brl=net,
            description=description,
        )

        if not pix_out.get("success"):
            intent.settlement_status = "SETTLEMENT_FAILED"
            intent.save(update_fields=["settlement_status"])
            return SettlementResult(
                False,
                gross,
                net,
                fee,
                None,
                pix_out.get("error") or "pix_failed",
            )

        txid = pix_out.get("txid") or ""
        PixTransaction.objects.create(
            intent=intent,
            tx_id=txid,
            status=str(pix_out.get("status") or "PROCESSING"),
            payload=pix_out.get("raw") or pix_out,
        )

        intent.amount_brl = gross
        intent.settled_amount_brl = net
        intent.settlement_fee_brl = fee
        intent.settlement_pix_txid = txid
        intent.settlement_status = "SETTLED"
        intent.status = "SETTLED"
        intent.metadata = {
            **intent.metadata,
            "settlement_at": timezone.now().isoformat(),
            "settlement_gross_brl": str(gross),
            "settlement_net_brl": str(net),
            "settlement_fee_brl": str(fee),
        }
        intent.save(
            update_fields=[
                "amount_brl",
                "settled_amount_brl",
                "settlement_fee_brl",
                "settlement_pix_txid",
                "settlement_status",
                "status",
                "metadata",
            ]
        )

        logger.info(
            "Settlement completed",
            extra={
                "intent_id": intent.intent_id,
                "net_brl": str(net),
                "pix_txid": txid,
            },
        )

        return SettlementResult(
            success=True,
            gross_brl=gross,
            net_brl=net,
            fee_brl=fee,
            pix_txid=txid,
            error=None,
        )
