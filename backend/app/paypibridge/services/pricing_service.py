"""
Pricing / câmbio para liquidação Pi → BRL.
Delega no FXService (taxa fixa, API ou custom conforme env).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from .fx_service import get_fx_service

logger = logging.getLogger(__name__)


class PricingService:
    """Fachada única de preço para o motor de liquidação."""

    def get_rate(self, from_currency: str = "PI", to_currency: str = "BRL") -> Optional[Decimal]:
        return get_fx_service().get_rate(from_currency, to_currency)

    def convert_pi_to_brl(self, amount_pi: Decimal) -> Optional[Decimal]:
        return get_fx_service().convert(amount_pi)


def get_pricing_service() -> PricingService:
    return PricingService()
