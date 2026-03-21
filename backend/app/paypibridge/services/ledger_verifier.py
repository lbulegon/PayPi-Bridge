"""
Consulta opcional ao Horizon (API HTTP Stellar-compatible) para cruzar txid no ledger.

Atenção: Pi Network tem rede própria; o URL do Horizon deve apontar para a instância
que indexa o ledger Pi (não usar horizon-testnet.stellar.org para transações Pi reais).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class LedgerVerificationResult:
    found: bool
    amount: Optional[Decimal]
    memo: Optional[str]
    source: Optional[str]
    destination: Optional[str]
    timestamp: Optional[str]
    raw_error: Optional[str] = None


class LedgerVerifier:
    def __init__(self, horizon_url: str, timeout: float = 10.0):
        self.horizon_url = horizon_url.rstrip("/")
        self.timeout = timeout

    def verify_transaction(self, txid: str) -> LedgerVerificationResult:
        if not txid or not self.horizon_url:
            return LedgerVerificationResult(
                False, None, None, None, None, None, "missing_txid_or_horizon_url"
            )
        try:
            tx_url = f"{self.horizon_url}/transactions/{txid}"
            tx_res = requests.get(tx_url, timeout=self.timeout)
            if tx_res.status_code != 200:
                return LedgerVerificationResult(
                    False,
                    None,
                    None,
                    None,
                    None,
                    None,
                    f"http_{tx_res.status_code}",
                )

            tx_data = tx_res.json()
            ops_url = f"{self.horizon_url}/transactions/{txid}/operations"
            ops_res = requests.get(ops_url, timeout=self.timeout)

            amount: Optional[Decimal] = None
            destination: Optional[str] = None

            if ops_res.status_code == 200:
                ops_data = ops_res.json()
                records = ops_data.get("_embedded", {}).get("records", [])
                for op in records:
                    if op.get("type") == "payment":
                        try:
                            amount = Decimal(str(op.get("amount", "0")))
                        except (InvalidOperation, TypeError, ValueError):
                            amount = None
                        destination = op.get("to") or op.get("destination")
                        break

            return LedgerVerificationResult(
                found=True,
                amount=amount,
                memo=tx_data.get("memo"),
                source=tx_data.get("source_account"),
                destination=destination,
                timestamp=tx_data.get("created_at"),
            )
        except requests.RequestException as e:
            logger.warning("Ledger Horizon request failed: %s", e, exc_info=True)
            return LedgerVerificationResult(
                False, None, None, None, None, None, str(e)
            )
        except Exception as e:
            logger.warning("Ledger verification error: %s", e, exc_info=True)
            return LedgerVerificationResult(
                False, None, None, None, None, None, str(e)
            )

    def to_dict(self, result: LedgerVerificationResult) -> dict[str, Any]:
        return {
            "found": result.found,
            "amount": str(result.amount) if result.amount is not None else None,
            "memo": result.memo,
            "source": result.source,
            "destination": result.destination,
            "timestamp": result.timestamp,
            "error": result.raw_error,
        }
