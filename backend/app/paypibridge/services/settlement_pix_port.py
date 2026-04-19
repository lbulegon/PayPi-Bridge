"""
Porta de envio Pix para liquidação (OpenPix, mock Open Finance ou cliente OF real).
"""

from __future__ import annotations

import logging
import uuid
from decimal import Decimal
from typing import Any, Dict, Optional

import os

from app.paypibridge.clients.pix import PixClient
from app.paypibridge.clients.openpix import OpenPixClient
from app.paypibridge.models import Consent

logger = logging.getLogger(__name__)


def _pix_provider() -> str:
    return (os.getenv("PIX_PROVIDER") or "").strip().lower()


def _use_openpix() -> bool:
    if _pix_provider() != "openpix":
        return False
    return OpenPixClient().is_configured()


def _of_mock() -> bool:
    if _use_openpix():
        return False
    return (os.getenv("OF_USE_MOCK", "true").lower() in ("1", "true", "yes")) or not (
        os.getenv("OF_BASE_URL") or ""
    ).strip()


class SettlementPixPort:
    """
    Envia Pix para liquidação. Em mock devolve sucesso sintético;
    com consent ativo usa PixClient (Open Finance).
    """

    def send(
        self,
        *,
        consent: Consent,
        cpf: str,
        pix_key: str,
        amount_brl: Decimal,
        description: str = "",
    ) -> Dict[str, Any]:
        amount_str = str(amount_brl.quantize(Decimal("0.01")))
        if _pix_provider() == "openpix" and not OpenPixClient().is_configured():
            logger.error("PIX_PROVIDER=openpix but OPENPIX_APP_ID or OPENPIX_FROM_PIX_KEY missing")
            return {
                "success": False,
                "error": "openpix_not_configured",
                "txid": None,
                "status": None,
            }

        if _use_openpix():
            op = OpenPixClient()
            logger.info(
                "Settlement Pix (OpenPix)",
                extra={"amount_brl": amount_str, "to_key_suffix": pix_key[-8:] if len(pix_key) > 8 else "***"},
            )
            result = op.transfer_to_pix_key(
                to_pix_key=pix_key,
                amount_brl=amount_brl,
                description=description or "PayPi-Bridge settlement",
            )
            return {
                "success": result.get("success", False),
                "txid": result.get("txid") or "",
                "status": result.get("status") or "UNKNOWN",
                "raw": result.get("raw"),
                "error": result.get("error"),
                "provider": "openpix",
            }

        if _of_mock():
            txid = f"mock_{uuid.uuid4().hex[:24]}"
            logger.info(
                "Settlement Pix (mock)",
                extra={"txid": txid, "amount_brl": amount_str},
            )
            return {"success": True, "txid": txid, "status": "PROCESSING", "mock": True}

        try:
            pix = PixClient.from_env(consent=consent)
            result = pix.create_immediate_payment(
                cpf=cpf,
                pix_key=pix_key,
                amount_brl=amount_str,
                description=description or "PayPi-Bridge settlement",
            )
            txid = result.get("txid") or result.get("payment_id") or ""
            return {
                "success": bool(txid),
                "txid": txid,
                "status": result.get("status", "UNKNOWN"),
                "raw": result,
            }
        except Exception as e:
            logger.exception("Settlement Pix failed")
            return {"success": False, "error": str(e), "txid": None, "status": None}
