"""
Orquestra confiança após a Pi Platform confirmar o pagamento: opcionalmente cruza com Horizon.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional, TYPE_CHECKING

from django.conf import settings

from .ledger_verifier import LedgerVerifier, LedgerVerificationResult

if TYPE_CHECKING:
    from .pi_service import PiService

logger = logging.getLogger(__name__)

# Níveis persistidos em PaymentIntent.confidence_level (alinhado ao desenho "trust engine")
CONFIDENCE_MEDIUM_TRUST = "medium_trust"  # Pi Platform verificada
CONFIDENCE_HIGH_TRUST = "high_trust"  # Pi Platform + tx encontrada no Horizon
CONFIDENCE_LEDGER_FAILED = "medium_trust_ledger_unavailable"  # Pi ok; Horizon falhou rede/HTTP
CONFIDENCE_LEDGER_NOT_FOUND = "medium_trust_ledger_tx_not_found"  # Pi ok; txid não no ledger


def get_ledger_verifier() -> Optional[LedgerVerifier]:
    if not getattr(settings, "ENABLE_LEDGER_VERIFICATION", False):
        return None
    base = (getattr(settings, "HORIZON_URL", None) or "").strip().rstrip("/")
    if not base:
        logger.warning(
            "ENABLE_LEDGER_VERIFICATION is true but HORIZON_URL is empty; ledger check skipped"
        )
        return None
    timeout = float(getattr(settings, "LEDGER_VERIFY_TIMEOUT", 10))
    return LedgerVerifier(base, timeout=timeout)


class PaymentTrustOrchestrator:
    """
    Usar depois de a Pi Platform indicar pagamento verificado on-chain.
    """

    def __init__(
        self,
        pi_service: PiService,
        ledger_verifier: Optional[LedgerVerifier] = None,
    ):
        self.pi_service = pi_service
        self.ledger_verifier = ledger_verifier

    def evaluate_platform_verified(
        self,
        *,
        payment: Dict[str, Any],
        payment_id: str,
        intent_amount_pi: Decimal,
        txid: Optional[str],
        strict_amount_match: bool = False,
    ) -> Dict[str, Any]:
        """
        payment: resposta de PiService.verify_payment (já validada como transaction_verified).
        txid: hash da transação; se None, tenta extrair de payment['transaction']['txid'].
        """
        resolved_txid = (txid or "").strip() or (
            (payment.get("transaction") or {}).get("txid") or ""
        ).strip()

        confidence = CONFIDENCE_MEDIUM_TRUST
        ledger_result: Optional[LedgerVerificationResult] = None

        if self.ledger_verifier and resolved_txid:
            ledger_result = self.ledger_verifier.verify_transaction(resolved_txid)
            if not ledger_result.found:
                err = ledger_result.raw_error or ""
                if err.startswith("http_404"):
                    confidence = CONFIDENCE_LEDGER_NOT_FOUND
                else:
                    confidence = CONFIDENCE_LEDGER_FAILED
            else:
                confidence = CONFIDENCE_HIGH_TRUST
                if strict_amount_match and ledger_result.amount is not None:
                    try:
                        delta = abs(ledger_result.amount - intent_amount_pi)
                        if delta > Decimal("0.0000001"):
                            return {
                                "status": "failed",
                                "reason": "amount_mismatch",
                                "confidence_level": confidence,
                                "ledger_checked": True,
                                "txid": resolved_txid,
                                "expected_pi": str(intent_amount_pi),
                                "ledger_amount_pi": str(ledger_result.amount),
                            }
                    except Exception as e:
                        logger.warning("Amount compare failed: %s", e)
                        return {
                            "status": "failed",
                            "reason": "amount_compare_error",
                            "detail": str(e),
                            "txid": resolved_txid,
                        }

        elif self.ledger_verifier and not resolved_txid:
            logger.info(
                "Ledger verification enabled but no txid; staying at medium_trust",
                extra={"payment_id": payment_id},
            )

        ledger_verified = bool(ledger_result and ledger_result.found)
        out: Dict[str, Any] = {
            "status": "approved",
            "confidence_level": confidence,
            "ledger_checked": ledger_verified,
            "txid": resolved_txid or None,
            "payment_id": payment_id,
        }
        if ledger_result and logger.isEnabledFor(logging.DEBUG):
            out["ledger"] = {
                "found": ledger_result.found,
                "amount": str(ledger_result.amount)
                if ledger_result.amount is not None
                else None,
                "error": ledger_result.raw_error,
            }
        return out
