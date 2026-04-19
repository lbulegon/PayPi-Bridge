"""
Cliente OpenPix (Woovi/Gerencianet) — transferência Pix entre chaves.

Documentação: POST /api/v1/transfer — value (centavos), fromPixKey, toPixKey.
Autenticação: header Authorization com o AppID (painel API/Plugins).

Requer habilitação da funcionalidade de transferência na conta OpenPix (pode estar em BETA).
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


class OpenPixClient:
    def __init__(self) -> None:
        self.app_id = (os.getenv("OPENPIX_APP_ID") or "").strip()
        self.base_url = (
            os.getenv("OPENPIX_BASE_URL") or "https://api.openpix.com.br/api/v1"
        ).rstrip("/")
        self.from_pix_key = (os.getenv("OPENPIX_FROM_PIX_KEY") or "").strip()
        self.timeout = int(os.getenv("OPENPIX_TIMEOUT", "30"))

    def is_configured(self) -> bool:
        return bool(self.app_id and self.from_pix_key)

    def transfer_to_pix_key(
        self,
        *,
        to_pix_key: str,
        amount_brl: Decimal,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Envia Pix da chave de origem (conta OpenPix) para a chave de destino.
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "openpix_not_configured",
                "txid": None,
                "status": None,
            }

        key = (to_pix_key or "").strip()
        if not key:
            return {
                "success": False,
                "error": "empty_pix_key",
                "txid": None,
                "status": None,
            }

        value_centavos = int((amount_brl * Decimal("100")).quantize(Decimal("1")))
        if value_centavos < 1:
            return {
                "success": False,
                "error": "invalid_amount",
                "txid": None,
                "status": None,
            }

        payload: Dict[str, Any] = {
            "value": value_centavos,
            "fromPixKey": self.from_pix_key,
            "toPixKey": key,
        }
        if description:
            payload["comment"] = description[:140]

        headers = {
            "Authorization": self.app_id,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        url = f"{self.base_url}/transfer"
        try:
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            logger.warning("OpenPix request failed: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "txid": None,
                "status": None,
            }

        try:
            body = resp.json() if resp.content else {}
        except ValueError:
            body = {"raw": resp.text[:500]}

        if not (200 <= resp.status_code < 300):
            err = None
            if isinstance(body, dict):
                errs = body.get("errors")
                if isinstance(errs, list) and errs:
                    err = errs[0].get("message") if isinstance(errs[0], dict) else str(errs[0])
                else:
                    err = body.get("message")
            logger.warning(
                "OpenPix transfer HTTP %s: %s",
                resp.status_code,
                err or resp.text[:300],
            )
            return {
                "success": False,
                "error": err or f"http_{resp.status_code}",
                "txid": None,
                "status": None,
                "raw": body,
            }

        tx = body.get("transaction") if isinstance(body, dict) else None
        correlation = None
        if isinstance(tx, dict):
            correlation = tx.get("correlationID") or tx.get("correlationId")
        txid = correlation or (str(tx.get("id")) if isinstance(tx, dict) and tx.get("id") else "")

        return {
            "success": bool(txid),
            "txid": txid or "",
            "status": "PROCESSING",
            "raw": body,
        }
